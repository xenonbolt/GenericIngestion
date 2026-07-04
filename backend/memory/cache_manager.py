from pymongo import MongoClient
import hashlib

class CacheManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/"):
        try:
            self.client = MongoClient(uri)
            self.db = self.client["ai_agent_db"]
            self.collection = self.db["answer_cache"]
        except Exception as e:
            print(f"Failed to connect to MongoDB Cache: {e}")
            self.collection = None

    def _hash_query(self, query: str) -> str:
        # Normalize and hash the query for consistent lookups
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def get_cached_answer(self, query: str):
        if self.collection is None:
            return None
        q_hash = self._hash_query(query)
        result = self.collection.find_one({"_id": q_hash})
        if result:
            return result.get("answer")
        return None

    def set_cached_answer(self, query: str, answer: str):
        if self.collection is None:
            return
        q_hash = self._hash_query(query)
        self.collection.update_one(
            {"_id": q_hash},
            {"$set": {"answer": answer, "original_query": query}},
            upsert=True
        )

    def clear_cache(self):
        if self.collection is not None:
            self.collection.delete_many({})
            print("Answer cache completely cleared due to data update.")

cache_manager = CacheManager()
