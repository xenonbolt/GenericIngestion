import os
import chromadb
import uuid
import numpy as np

class VectorMemoryManager:
    def __init__(self, path: str = "./chroma_db"):
        self.chroma_client = chromadb.PersistentClient(path=path)
        # We will create a single collection for all users, filtering by user_id metadata
        self.collection = self.chroma_client.get_or_create_collection(name="user_long_term_memory")
        self._configured_google = False
        self._openai_embeddings = None

    def _embed(self, text: str) -> list[float]:
        """Embeds text using the configured LLM provider."""
        llm_provider = os.getenv("LLM_PROVIDER", "google").lower()
        if llm_provider == "openai":
            if not self._openai_embeddings:
                from langchain_openai import OpenAIEmbeddings
                embed_model = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
                self._openai_embeddings = OpenAIEmbeddings(model=embed_model)
            try:
                return self._openai_embeddings.embed_query(text)
            except Exception as e:
                print(f"[VectorMemory] OpenAI Embedding error: {e}")
                return None
        else:
            if not self._configured_google:
                import google.generativeai as genai
                api_key = os.getenv("GOOGLE_API_KEY")
                if api_key:
                    genai.configure(api_key=str(api_key))
                self._configured_google = True
            
            import google.generativeai as genai
            embed_model = os.getenv("EMBEDDING_MODEL_NAME", "models/gemini-embedding-001")
            try:
                result = genai.embed_content(model=embed_model, content=text)
                return result["embedding"]
            except Exception as e:
                print(f"[VectorMemory] Google Embedding error: {e}")
                return None

    def add_memory(self, user_id: str, memory_text: str):
        """Stores a new fact/memory for the user."""
        embedding = self._embed(memory_text)
        if not embedding:
            return

        memory_id = str(uuid.uuid4())
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[memory_text],
            metadatas=[{"user_id": user_id, "type": "fact"}]
        )
        print(f"[VectorMemory] Added for {user_id}: {memory_text}")

    def search_memory(self, user_id: str, query: str, top_k: int = 5) -> list[str]:
        """Retrieves top K most relevant facts for the user based on the query."""
        embedding = self._embed(query)
        if not embedding:
            return []

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where={"user_id": user_id}
        )
        
        if results and results['documents'] and results['documents'][0]:
            # Also check distances to filter out irrelevant stuff
            distances = results['distances'][0]
            docs = results['documents'][0]
            
            # ChromaDB cosine distance (smaller is better). 
            # We'll return docs that are reasonably close.
            valid_memories = []
            for i in range(len(docs)):
                # L2 distance or cosine depending on chroma setup. 
                # Let's just return all top K for now, prompt will filter.
                valid_memories.append(docs[i])
            return valid_memories
        return []

    def delete_memory(self, user_id: str, memory_text: str):
        """Deletes a specific memory text by doing a semantic search for the closest match and removing it."""
        embedding = self._embed(memory_text)
        if not embedding:
            return

        # Find the absolute closest memory
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=1,
            where={"user_id": user_id}
        )
        
        if results and results['ids'] and results['ids'][0]:
            memory_id = results['ids'][0][0]
            matched_doc = results['documents'][0][0]
            self.collection.delete(ids=[memory_id])
            print(f"[VectorMemory] Deleted for {user_id}: {matched_doc}")

    def update_memory(self, user_id: str, old_memory: str, new_memory: str):
        """Semantically finds the old memory, deletes it, and adds the new one."""
        self.delete_memory(user_id, old_memory)
        self.add_memory(user_id, new_memory)

