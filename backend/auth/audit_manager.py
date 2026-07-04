from pymongo import MongoClient
from datetime import datetime

class AuditManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "agentic_platform"):
        self.client = MongoClient(uri)
        self.collection = self.client[db_name]["audit_logs"]

    def log_action(self, user_id: str, action: str, details: str = ""):
        self.collection.insert_one({
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "action": action,
            "details": details
        })

    def get_logs(self, limit: int = 100):
        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        return [{
            "id": str(doc["_id"]),
            "timestamp": doc["timestamp"].isoformat(),
            "user_id": doc["user_id"],
            "action": doc["action"],
            "details": doc["details"]
        } for doc in cursor]

audit_manager = AuditManager()
