import os
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Any

class MongoMemoryManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "agentic_platform"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.short_term = self.db["short_term_memory"] # Stores conversation turns
        self.long_term = self.db["long_term_memory"]   # Stores user preferences/facts
        
        # In-memory caches to reduce DB load
        self._history_cache = {}
        self._facts_cache = {}

    def add_message(self, session_id: str, user_id: str, role: str, content: str):
        message = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        self.short_term.insert_one(message)
        
        if session_id in self._history_cache:
            self._history_cache[session_id].append({"role": role, "content": content})

    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        if session_id in self._history_cache:
            return self._history_cache[session_id]
            
        cursor = self.short_term.find({"session_id": session_id}).sort("timestamp", 1).limit(limit)
        messages = [{"role": msg["role"], "content": msg["content"], "timestamp": msg.get("timestamp", datetime.utcnow()).isoformat()} for msg in cursor]
        self._history_cache[session_id] = messages
        return messages

    def delete_session(self, session_id: str):
        self.short_term.delete_many({"session_id": session_id})
        if session_id in self._history_cache:
            del self._history_cache[session_id]

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"timestamp": 1}},
            {"$group": {
                "_id": "$session_id",
                "first_message": {"$first": "$content"},
                "started_at": {"$first": "$timestamp"},
                "last_active": {"$last": "$timestamp"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_active": -1}}
        ]
        results = list(self.short_term.aggregate(pipeline))
        return [{
            "session_id": r["_id"],
            "title": r["first_message"][:40] + "..." if len(r["first_message"]) > 40 else r["first_message"],
            "started_at": r["started_at"].isoformat() if r["started_at"] else None,
            "last_active": r["last_active"].isoformat() if r["last_active"] else None,
            "message_count": r["message_count"]
        } for r in results]

    def save_long_term_fact(self, user_id: str, key: str, value: Any):
        self.long_term.update_one(
            {"user_id": user_id},
            {"$set": {key: value, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        
        if user_id not in self._facts_cache:
            self.get_long_term_facts(user_id) # force load into cache
        self._facts_cache[user_id][key] = value

    def get_long_term_facts(self, user_id: str) -> Dict[str, Any]:
        if user_id in self._facts_cache:
            return self._facts_cache[user_id]
            
        record = self.long_term.find_one({"user_id": user_id})
        facts = {}
        if record:
            record.pop("_id", None)
            record.pop("user_id", None)
            record.pop("updated_at", None)
            facts = record
            
        self._facts_cache[user_id] = facts
        return facts

    def extract_and_save_preferences(self, user_id: str, content: str):
        # A simple mock logic for extracting preferences. 
        # In a real agent, this would use an LLM call to extract facts.
        content_lower = content.lower()
        if "my name is" in content_lower:
            name = content_lower.split("my name is")[-1].strip().split()[0]
            self.save_long_term_fact(user_id, "name", name)
        if "i like" in content_lower:
            likes = content_lower.split("i like")[-1].strip()
            self.save_long_term_fact(user_id, "likes", likes)
