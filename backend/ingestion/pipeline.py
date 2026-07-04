import os
import io
import uuid
import base64
import chromadb
from typing import Dict, Any, List
from graph.networkx_store import kg_store
from graph.kuzu_store import kuzu_store
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

class DataIngestionPipeline:
    def __init__(self):
        # Initialize Vector Store (ChromaDB)
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="unstructured_docs")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        
        # Load multimodal LLM for media extraction if needed
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2)
        
        # Check strategy
        self.native_media = os.getenv("NATIVE_MEDIA_EXTRACTION", "false").lower() == "true"

    def ingest_csv_to_graph(self, file_path: str, entity_col: str = "source", relation_col: str = "relation", target_col: str = "target"):
        """Ingests structured CSV data into the NetworkX and Kuzu knowledge graphs."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        kg_store.ingest_csv(file_path, entity_col, relation_col, target_col)
        kuzu_store.ingest_csv(file_path, entity_col, relation_col, target_col)
        print("CSV Ingestion Complete.")

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        reader = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def _extract_text_from_media_gemini(self, file_content: bytes, mime_type: str, file_name: str) -> str:
        """Uses Gemini directly to extract text/summary from image/audio/video."""
        encoded_data = base64.b64encode(file_content).decode('utf-8')
        
        msg = HumanMessage(
            content=[
                {"type": "text", "text": f"Please extract all text and summarize the contents of this {mime_type} file named {file_name}. Give a highly detailed transcription and semantic summary."},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_data}"}}
            ]
        )
        response = self.llm.invoke([msg])
        return response.content

    def _extract_text_from_media_native(self, file_content: bytes, mime_type: str, file_name: str, ext: str) -> str:
        """Native extraction using whisper and moviepy."""
        # For simplicity in this demo, if native is enabled, write to temp file and process
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name

        text = ""
        try:
            if "video" in mime_type:
                from moviepy.editor import VideoFileClip
                video = VideoFileClip(temp_path)
                audio_path = temp_path + ".wav"
                video.audio.write_audiofile(audio_path, logger=None)
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                text = result["text"]
                os.remove(audio_path)
            elif "audio" in mime_type:
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(temp_path)
                text = result["text"]
        except Exception as e:
            text = f"Failed native extraction: {e}"
        finally:
            os.remove(temp_path)
            
        return text

    def ingest_unstructured_file(self, file_name: str, file_content: bytes, mime_type: str, metadata: Dict[str, Any]):
        """Ingests unstructured file, extracts text, chunks it, and saves to VectorDB. Also links to Graph."""
        print(f"Ingesting unstructured file: {file_name} ({mime_type})")
        doc_id = str(uuid.uuid4())
        extracted_text = ""

        # 1. Extraction Phase
        if mime_type == "application/pdf":
            extracted_text = self._extract_text_from_pdf(file_content)
        elif mime_type == "text/plain" or mime_type == "text/markdown" or mime_type == "text/csv":
            # For plain text (if CSV is passed as unstructured, just treat as text)
            extracted_text = file_content.decode('utf-8', errors='ignore')
        elif "image" in mime_type or "audio" in mime_type or "video" in mime_type:
            ext = os.path.splitext(file_name)[1]
            if self.native_media and ("audio" in mime_type or "video" in mime_type):
                extracted_text = self._extract_text_from_media_native(file_content, mime_type, file_name, ext)
            else:
                extracted_text = self._extract_text_from_media_gemini(file_content, mime_type, file_name)
        else:
            extracted_text = file_content.decode('utf-8', errors='ignore')

        # 2. Chunking & Vector DB Phase
        if extracted_text.strip():
            chunks = self.text_splitter.split_text(extracted_text)
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{**metadata, "file_name": file_name, "chunk_index": i} for i in range(len(chunks))]
            
            # ChromaDB handles embeddings natively by default using all-MiniLM-L6-v2, or we can use our LLM embeddings.
            # We will use Chroma's default for simplicity.
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )

        # 3. Graph Database Linking
        # Add the document as a node in the Knowledge Graph
        kg_store.add_entity(file_name, {"type": "Document", "mime_type": mime_type, "doc_id": doc_id, **metadata})
        kuzu_store.add_entity(file_name, {"type": "Document", "mime_type": mime_type, "doc_id": doc_id, **metadata})
        
        # Link the tags if they exist
        tags = metadata.get("tags", "")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tags:
            kg_store.add_entity(tag, {"type": "Tag"})
            kg_store.add_relationship(file_name, tag, "HAS_TAG")
            
            kuzu_store.add_entity(tag, {"type": "Tag"})
            kuzu_store.add_relationship(file_name, tag, "HAS_TAG")

        return doc_id

    def ingest_tabular_file(self, file_name: str, file_content: bytes, mime_type: str, metadata: Dict[str, Any]):
        """Saves tabular data directly to disk for Pandas querying and logs it in the knowledge graph."""
        print(f"Ingesting tabular file: {file_name}")
        doc_id = str(uuid.uuid4())
        
        # Save securely to uploads directory
        uploads_dir = os.path.join(os.getcwd(), "data", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        safe_name = f"{doc_id}_{file_name}"
        file_path = os.path.join(uploads_dir, safe_name)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        # Add the document as a node in the Knowledge Graph for tracking
        kg_store.add_entity(file_name, {
            "type": "TabularData", 
            "mime_type": mime_type, 
            "doc_id": doc_id, 
            "file_path": file_path,
            **metadata
        })
        kuzu_store.add_entity(file_name, {
            "type": "TabularData", 
            "mime_type": mime_type, 
            "doc_id": doc_id, 
            "file_path": file_path,
            **metadata
        })
        
        return doc_id

pipeline = DataIngestionPipeline()
