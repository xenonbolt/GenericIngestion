import os
import json
import logging
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("MongoMemory")

class MongoMemoryManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "agentic_platform"):
        self.use_fallback = False
        self.fallback_dir = os.path.join(os.getcwd(), "data", "fallback_db")
        os.makedirs(self.fallback_dir, exist_ok=True)
        
        # In-memory caches
        self._history_cache = {}
        self._facts_cache = {}
        
        try:
            logger.info("Connecting to MongoDB for conversation memory...")
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            # Force a ping to check if server is active
            self.client.admin.command('ping')
            
            self.db = self.client[db_name]
            self.short_term = self.db["short_term_memory"] 
            self.long_term = self.db["long_term_memory"]   
            self.summaries = self.db["session_summaries"]  
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}. Switching to local JSON database fallback.")
            self.use_fallback = True
            self._init_fallback_files()

    def _init_fallback_files(self):
        self.short_term_path = os.path.join(self.fallback_dir, "short_term.json")
        self.long_term_path = os.path.join(self.fallback_dir, "long_term.json")
        self.summaries_path = os.path.join(self.fallback_dir, "summaries.json")
        
        for path in [self.short_term_path, self.long_term_path, self.summaries_path]:
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump([] if path == self.short_term_path else {}, f)

    def _read_fallback(self, path: str) -> Any:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return [] if path == self.short_term_path else {}

    def _write_fallback(self, path: str, data: Any):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write fallback data to {path}: {e}")

    def add_message(self, session_id: str, user_id: str, role: str, content: str):
        if self.use_fallback:
            messages = self._read_fallback(self.short_term_path)
            new_msg = {
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            messages.append(new_msg)
            self._write_fallback(self.short_term_path, messages)
            
            if session_id in self._history_cache:
                self._history_cache[session_id].append({"role": role, "content": content})
            return

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
            
        if self.use_fallback:
            all_messages = self._read_fallback(self.short_term_path)
            session_messages = [
                {"role": m["role"], "content": m["content"], "timestamp": m["timestamp"]} 
                for m in all_messages if m["session_id"] == session_id
            ]
            session_messages = session_messages[-limit:]
            self._history_cache[session_id] = session_messages
            return session_messages

        cursor = self.short_term.find({"session_id": session_id}).sort("timestamp", 1).limit(limit)
        messages = [{"role": msg["role"], "content": msg["content"], "timestamp": msg.get("timestamp", datetime.utcnow()).isoformat()} for msg in cursor]
        self._history_cache[session_id] = messages
        return messages

    def delete_session(self, session_id: str):
        if self.use_fallback:
            all_messages = self._read_fallback(self.short_term_path)
            filtered = [m for m in all_messages if m["session_id"] != session_id]
            self._write_fallback(self.short_term_path, filtered)
            
            summaries = self._read_fallback(self.summaries_path)
            if session_id in summaries:
                del summaries[session_id]
                self._write_fallback(self.summaries_path, summaries)
                
            if session_id in self._history_cache:
                del self._history_cache[session_id]
            return

        self.short_term.delete_many({"session_id": session_id})
        self.summaries.delete_one({"session_id": session_id})
        if session_id in self._history_cache:
            del self._history_cache[session_id]

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        if self.use_fallback:
            all_messages = self._read_fallback(self.short_term_path)
            user_msg = [m for m in all_messages if m["user_id"] == user_id]
            
            sessions = {}
            for m in user_msg:
                sid = m["session_id"]
                if sid not in sessions:
                    sessions[sid] = {
                        "session_id": sid,
                        "first_message": m["content"],
                        "started_at": m["timestamp"],
                        "last_active": m["timestamp"],
                        "message_count": 0
                    }
                sessions[sid]["last_active"] = m["timestamp"]
                sessions[sid]["message_count"] += 1
                
            result = list(sessions.values())
            # Sort by last active descending
            result.sort(key=lambda x: x["last_active"], reverse=True)
            return [{
                "session_id": r["session_id"],
                "title": r["first_message"][:40] + "..." if len(r["first_message"]) > 40 else r["first_message"],
                "started_at": r["started_at"],
                "last_active": r["last_active"],
                "message_count": r["message_count"]
            } for r in result]

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
        if self.use_fallback:
            facts = self._read_fallback(self.long_term_path)
            if user_id not in facts:
                facts[user_id] = {}
            facts[user_id][key] = value
            self._write_fallback(self.long_term_path, facts)
            self._facts_cache[user_id] = facts[user_id]
            return

        self.long_term.update_one(
            {"user_id": user_id},
            {"$set": {key: value, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        if user_id not in self._facts_cache:
            self.get_long_term_facts(user_id) 
        self._facts_cache[user_id][key] = value

    def get_long_term_facts(self, user_id: str) -> Dict[str, Any]:
        if user_id in self._facts_cache:
            return self._facts_cache[user_id]
            
        if self.use_fallback:
            facts = self._read_fallback(self.long_term_path)
            user_facts = facts.get(user_id, {})
            self._facts_cache[user_id] = user_facts
            return user_facts

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
        content_lower = content.lower()
        if "my name is" in content_lower:
            name = content_lower.split("my name is")[-1].strip().split()[0]
            self.save_long_term_fact(user_id, "name", name)
        if "i like" in content_lower:
            likes = content_lower.split("i like")[-1].strip()
            self.save_long_term_fact(user_id, "likes", likes)

    def get_session_summary(self, session_id: str) -> str:
        if self.use_fallback:
            summaries = self._read_fallback(self.summaries_path)
            return summaries.get(session_id, "")
            
        record = self.summaries.find_one({"session_id": session_id})
        return record.get("summary", "") if record else ""

    def update_session_summary(self, session_id: str, new_summary: str):
        if self.use_fallback:
            summaries = self._read_fallback(self.summaries_path)
            summaries[session_id] = new_summary
            self._write_fallback(self.summaries_path, summaries)
            return

        self.summaries.update_one(
            {"session_id": session_id},
            {"$set": {"summary": new_summary, "updated_at": datetime.utcnow()}},
            upsert=True
        )
