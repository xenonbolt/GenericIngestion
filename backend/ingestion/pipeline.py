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
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pypdf import PdfReader
from dotenv import load_dotenv
from memory.mongo_memory import MongoMemoryManager
import json

load_dotenv()

class DataIngestionPipeline:
    def __init__(self):
        # Initialize Vector Store (ChromaDB)
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="unstructured_docs")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        self.mongo_memory = MongoMemoryManager()
        
        # Load multimodal LLM for media extraction if needed
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if self.llm_provider == "openai":
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
            # Setup kwargs for ChatOpenAI, including Headroom proxy if configured
            llm_kwargs = {
                "model": model_name,
                "temperature": 0.2
            }
            
            # Route requests through Headroom proxy if configured
            headroom_proxy = os.getenv("HEADROOM_PROXY")
            if headroom_proxy:
                llm_kwargs["base_url"] = headroom_proxy
                
            self.llm = ChatOpenAI(**llm_kwargs)
        else:
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
        extract_images = os.getenv("EXTRACT_PDF_IMAGES", "true").lower() == "true"
        
        for i, page in enumerate(reader.pages):
            text += f"\n--- Page {i+1} ---\n"
            text += page.extract_text() + "\n"
            
            if extract_images and page.images:
                for img in page.images:
                    try:
                        mime_type = "image/jpeg"
                        if img.name.lower().endswith(".png"):
                            mime_type = "image/png"
                        
                        encoded_data = base64.b64encode(img.data).decode('utf-8')
                        msg = HumanMessage(
                            content=[
                                {"type": "text", "text": "Describe this image, chart, or graph in detail. Extract any relevant text, numbers, or key insights."},
                                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_data}"}}
                            ]
                        )
                        response = self.llm.invoke([msg])
                        text += f"\n[Embedded Image Content: {response.content}]\n"
                    except Exception as e:
                        print(f"Error extracting image {img.name} on page {i+1}: {e}")
                        
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
                from moviepy import VideoFileClip
                with VideoFileClip(temp_path) as video:
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
            import traceback
            traceback.print_exc()
            text = f"Failed native extraction: {e}"
        finally:
            os.remove(temp_path)
            
        return text

    def ingest_unstructured_file(self, file_name: str, file_content: bytes, mime_type: str, metadata: Dict[str, Any]):
        """Ingests unstructured file, extracts text, chunks it, and saves to VectorDB. Also links to Graph."""
        print(f"Ingesting unstructured file: {file_name} ({mime_type})")
        doc_id = str(uuid.uuid4())
        extracted_text = ""
        
        try:
            from memory.cache_manager import cache_manager
            cache_manager.clear_cache()
        except Exception as e:
            print("Cache clear error:", e)

        # 1. Extraction Phase
        if mime_type == "application/pdf":
            extracted_text = self._extract_text_from_pdf(file_content)
        elif mime_type == "text/plain" or mime_type == "text/markdown" or mime_type == "text/csv":
            # For plain text (if CSV is passed as unstructured, just treat as text)
            extracted_text = file_content.decode('utf-8', errors='ignore')
        elif "image" in mime_type or "audio" in mime_type or "video" in mime_type:
            ext = os.path.splitext(file_name)[1]
            if self.llm_provider == "openai" and "image" not in mime_type:
                extracted_text = self._extract_text_from_media_native(file_content, mime_type, file_name, ext)
            elif self.native_media and ("audio" in mime_type or "video" in mime_type):
                extracted_text = self._extract_text_from_media_native(file_content, mime_type, file_name, ext)
            else:
                extracted_text = self._extract_text_from_media_gemini(file_content, mime_type, file_name)
        else:
            extracted_text = file_content.decode('utf-8', errors='ignore')

        # 2. Lazy Embedding Phase (Store raw text in Mongo, don't embed yet)
        if extracted_text.strip():
            print(f"Generating summary and keywords for lazy embedding: {file_name}")
            prompt = f"""Analyze the following document and provide a concise summary and a list of key topics/keywords.
Document text (first 5000 chars): {extracted_text[:5000]}

Output ONLY valid JSON:
{{
    "summary": "1-2 sentence summary of the document",
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""
            try:
                resp = self.llm.invoke([HumanMessage(content=prompt)])
                resp_text = resp.content.strip()
                if resp_text.startswith("```json"): resp_text = resp_text[7:]
                if resp_text.startswith("```"): resp_text = resp_text[3:]
                if resp_text.endswith("```"): resp_text = resp_text[:-3]
                parsed = json.loads(resp_text)
                summary = parsed.get("summary", "")
                keywords = parsed.get("keywords", [])
            except Exception as e:
                print(f"Failed to generate lazy embedding metadata: {e}")
                summary = "Failed to generate summary."
                keywords = []
                
            self.mongo_memory.save_raw_document(doc_id, file_name, extracted_text, summary, keywords, metadata)

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

        # 4. GraphRAG Chunk Entity Extraction is disabled during ingestion in Lazy Embed model.
        # GraphRAG will be handled dynamically if needed during the embedding phase.

        return doc_id

    def ingest_tabular_file(self, file_name: str, file_content: bytes, mime_type: str, metadata: Dict[str, Any]):
        """Saves tabular data directly to disk for Pandas querying and logs it in the knowledge graph."""
        print(f"Ingesting tabular file: {file_name}")
        doc_id = str(uuid.uuid4())
        
        try:
            from memory.cache_manager import cache_manager
            cache_manager.clear_cache()
        except Exception as e:
            print("Cache clear error:", e)
        
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
        
        # Save to master metadata for Graph Librarian routing
        import json
        master_metadata_path = os.path.join(os.getcwd(), "data", "master_chunk_metadata.json")
        master_metadata = {}
        if os.path.exists(master_metadata_path):
            with open(master_metadata_path, "r") as f:
                try:
                    master_metadata = json.load(f)
                except Exception:
                    pass
        
        master_metadata[doc_id] = {
            "type": "tabular",
            "file_name": file_name,
            "summary": metadata.get("summary", ""),
            "category": metadata.get("category", ""),
            "keywords": [k.strip() for k in metadata.get("tags", "").split(",") if k.strip()]
        }
        
        with open(master_metadata_path, "w") as f:
            json.dump(master_metadata, f, indent=2)
            
        return doc_id

    def _extract_graphrag_entities(self, file_name: str, chunks: List[str], chunk_ids: List[str]):
        """Uses LLM to extract entities, relations, summaries, and keywords from chunks."""
        import json
        import re
        
        ontology_path = os.path.join(os.getcwd(), "data", "ontology.json")
        ontology = {"entities": [], "relations": []}
        if os.path.exists(ontology_path):
            with open(ontology_path, "r") as f:
                try:
                    ontology = json.load(f)
                except Exception:
                    pass
                    
        master_metadata_path = os.path.join(os.getcwd(), "data", "master_chunk_metadata.json")
        master_metadata = {}
        if os.path.exists(master_metadata_path):
            with open(master_metadata_path, "r") as f:
                try:
                    master_metadata = json.load(f)
                except Exception:
                    pass
        
        for chunk, chunk_id in zip(chunks, chunk_ids):
            kg_store.add_entity(chunk_id, {"type": "Chunk", "text": chunk[:200] + "..."})
            kuzu_store.add_entity(chunk_id, {"type": "Chunk", "text": chunk[:200] + "..."})
            kg_store.add_relationship(file_name, chunk_id, "HAS_CHUNK")
            kuzu_store.add_relationship(file_name, chunk_id, "HAS_CHUNK")

            prompt = f"""You are a Graph Extraction bot. Analyze this text chunk and extract entities, relationships, a 1-line summary, and keywords.
Return ONLY valid JSON with no markdown wrapping.
Format:
{{
  "summary": "One line summary of the chunk",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "entities": [{{"name": "Entity Name", "type": "Person|Organization|Concept|etc"}}],
  "relationships": [{{"source": "Entity 1", "target": "Entity 2", "relation": "WORKS_FOR|OWNER_OF|etc"}}]
}}
Text Chunk:
{chunk}"""
            try:
                msg = HumanMessage(content=prompt)
                resp = self.llm.invoke([msg])
                
                json_match = re.search(r'\{.*\}', resp.content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    data = json.loads(resp.content)
                    
                # Update ChromaDB Metadata
                summary = str(data.get("summary", ""))
                keywords = ",".join(data.get("keywords", []))
                
                try:
                    existing_meta = self.collection.get(ids=[chunk_id])["metadatas"][0]
                    existing_meta["chunk_summary"] = summary
                    existing_meta["chunk_keywords"] = keywords
                    self.collection.update(ids=[chunk_id], metadatas=[existing_meta])
                except Exception as e:
                    print(f"Failed to update ChromaDB metadata for {chunk_id}: {e}")
                    
                # Save to master chunk metadata
                master_metadata[chunk_id] = {
                    "summary": summary,
                    "keywords": data.get("keywords", [])
                }
                
                for ent in data.get("entities", []):
                    name = str(ent.get("name", "")).strip()
                    etype = str(ent.get("type", "Concept")).strip()
                    if name:
                        kg_store.add_entity(name, {"type": etype})
                        kuzu_store.add_entity(name, {"type": etype})
                        kg_store.add_relationship(chunk_id, name, "MENTIONS")
                        kuzu_store.add_relationship(chunk_id, name, "MENTIONS")
                        
                        if etype not in ontology["entities"]:
                            ontology["entities"].append(etype)
                
                for rel in data.get("relationships", []):
                    src = str(rel.get("source", "")).strip()
                    tgt = str(rel.get("target", "")).strip()
                    rtype = str(rel.get("relation", "RELATED_TO")).strip().upper().replace(" ", "_")
                    if src and tgt:
                        kg_store.add_entity(src, {})
                        kg_store.add_entity(tgt, {})
                        kuzu_store.add_entity(src, {})
                        kuzu_store.add_entity(tgt, {})
                        
                        kg_store.add_relationship(src, tgt, rtype)
                        kuzu_store.add_relationship(src, tgt, rtype)
                        
                        if rtype not in ontology["relations"]:
                            ontology["relations"].append(rtype)
                            
            except Exception as e:
                print(f"GraphRAG Extraction Error on chunk {chunk_id}: {e}")
                
        with open(ontology_path, "w") as f:
            json.dump(ontology, f, indent=2)
            
        with open(master_metadata_path, "w") as f:
            json.dump(master_metadata, f, indent=2)

pipeline = DataIngestionPipeline()
