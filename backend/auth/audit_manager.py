import os
import json
import uuid
import logging
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger("AuditManager")

class AuditManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "agentic_platform"):
        self.use_fallback = False
        self.fallback_dir = os.path.join(os.getcwd(), "data", "fallback_db")
        os.makedirs(self.fallback_dir, exist_ok=True)
        self.logs_path = os.path.join(self.fallback_dir, "audit_logs.json")
        
        try:
            logger.info("Connecting to MongoDB for Audit Manager...")
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            
            self.collection = self.client[db_name]["audit_logs"]
            logger.info("Audit Manager connected to MongoDB successfully.")
        except Exception as e:
            logger.warning(f"MongoDB connection failed for Audit Manager: {e}. Using local JSON database fallback.")
            self.use_fallback = True
            self._init_fallback()

    def _init_fallback(self):
        if not os.path.exists(self.logs_path):
            with open(self.logs_path, "w") as f:
                json.dump([], f)

    def _read_fallback(self) -> list:
        try:
            with open(self.logs_path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_fallback(self, data: list):
        try:
            with open(self.logs_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write fallback audit logs: {e}")

    def log_action(self, user_id: str, action: str, details: str = ""):
        if self.use_fallback:
            logs = self._read_fallback()
            new_log = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "action": action,
                "details": details
            }
            logs.append(new_log)
            self._write_fallback(logs)
            return

        self.collection.insert_one({
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "action": action,
            "details": details
        })

    def get_logs(self, limit: int = 100):
        if self.use_fallback:
            logs = self._read_fallback()
            # Sort logs by timestamp descending
            logs.sort(key=lambda x: x["timestamp"], reverse=True)
            return logs[:limit]

        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        return [{
            "id": str(doc["_id"]),
            "timestamp": doc["timestamp"].isoformat(),
            "user_id": doc["user_id"],
            "action": doc["action"],
            "details": doc["details"]
        } for doc in cursor]

audit_manager = AuditManager()
