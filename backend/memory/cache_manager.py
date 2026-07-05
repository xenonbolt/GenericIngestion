from pymongo import MongoClient
import hashlib
import os
import numpy as np
import google.generativeai as genai
import re

# Pronouns and relative words that flag a query as context-dependent (never cache)
CONTEXT_DEPENDENT_MARKERS = [
    r"\babove\b", r"\bthose\b", r"\bthese\b", r"\bthem\b", r"\bthey\b", r"\btheir\b",
    r"\bmentioned\b", r"\blisted\b", r"\bprevious\b", r"\blast\b", r"\bearlier\b",
    r"\bit\b", r"\bits\b", r"\bhe\b", r"\bshe\b", r"\bhis\b", r"\bher\b", r"\bsame\b",
    r"\bthat\b", r"\bthis\b", r"\bsuch\b", r"can you get", r"get the", r"what about"
]

SEMANTIC_CACHE_THRESHOLD = 0.80  # Cosine similarity threshold to count as a cache hit


class CacheManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/"):
        try:
            self.client = MongoClient(uri)
            self.db = self.client["ai_agent_db"]
            self.collection = self.db["answer_cache"]
        except Exception as e:
            print(f"Failed to connect to MongoDB Cache: {e}")
            self.collection = None

        self._configured = False

    def _configure_genai(self):
        """Configure the google.generativeai SDK once, lazily."""
        if not self._configured:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=str(api_key))  # force plain str, no SecretStr
                self._configured = True

    def _is_context_dependent(self, query: str) -> bool:
        """Detect whether a query relies on conversation context and should never be cached."""
        q_lower = query.lower().strip()
        for marker_pattern in CONTEXT_DEPENDENT_MARKERS:
            if re.search(marker_pattern, q_lower):
                return True
        return False

    def _embed(self, text: str):
        llm_provider = os.getenv("LLM_PROVIDER", "google").lower()
        
        if llm_provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            embed_model = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
            try:
                embeddings = OpenAIEmbeddings(model=embed_model)
                result = embeddings.embed_query(text)
                return np.array(result)
            except Exception as e:
                print(f"[Cache] OpenAI Embedding error: {e}")
                return None
        else:
            """Embed a text string using google.generativeai directly (avoids LangChain SecretStr bug)."""
            self._configure_genai()
            if not self._configured:
                return None
            embed_model = os.getenv("EMBEDDING_MODEL_NAME", "models/gemini-embedding-001")
            try:
                result = genai.embed_content(model=embed_model, content=text)
                return np.array(result["embedding"])
            except Exception as e:
                print(f"[Cache] Google Embedding error: {e}")
                return None

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    def get_cached_answer(self, query: str):
        if self.collection is None:
            return None

        # Never serve cached answers for context-dependent follow-ups
        if self._is_context_dependent(query):
            print(f"[Cache] Skipping — context-dependent query: '{query[:60]}'")
            return None

        query_vec = self._embed(query)
        if query_vec is None:
            return None

        try:
            cached_docs = list(self.collection.find({}, {"original_query": 1, "answer": 1, "embedding": 1}))
            best_score = 0.0
            best_answer = None

            for doc in cached_docs:
                stored_vec = doc.get("embedding")
                if stored_vec is None:
                    continue
                similarity = self._cosine_similarity(query_vec, np.array(stored_vec))
                if similarity > best_score:
                    best_score = similarity
                    best_answer = doc.get("answer")

            if best_score >= SEMANTIC_CACHE_THRESHOLD:
                print(f"[Cache] HIT (similarity={best_score:.4f}) for: '{query[:60]}'")
                return best_answer
            else:
                print(f"[Cache] MISS (best={best_score:.4f}) for: '{query[:60]}'")
                return None

        except Exception as e:
            print(f"[Cache] Lookup error: {e}")
            return None

    def set_cached_answer(self, query: str, answer: str):
        if self.collection is None:
            return

        # Never cache context-dependent queries
        if self._is_context_dependent(query):
            return

        embedding = self._embed(query)
        if embedding is None:
            return

        q_hash = hashlib.sha256(query.lower().strip().encode("utf-8")).hexdigest()
        self.collection.update_one(
            {"_id": q_hash},
            {"$set": {
                "answer": answer,
                "original_query": query,
                "embedding": embedding.tolist()
            }},
            upsert=True
        )
        print(f"[Cache] Stored: '{query[:60]}'")

    def clear_cache(self):
        if self.collection is not None:
            self.collection.delete_many({})
            print("Answer cache completely cleared due to data update.")


cache_manager = CacheManager()
