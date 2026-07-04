from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import os

class ApprovalManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "agentic_platform"):
        self.client = MongoClient(uri)
        self.collection = self.client[db_name]["approvals"]

    def add_pending(self, file_path: str, filename: str, mime: str, metadata: dict, user_id: str):
        record = {
            "file_path": file_path,
            "filename": filename,
            "mime_type": mime,
            "metadata": metadata,
            "submitted_by": user_id,
            "status": "pending",
            "timestamp": datetime.utcnow()
        }
        result = self.collection.insert_one(record)
        return str(result.inserted_id)

    def get_pending(self):
        cursor = self.collection.find({"status": "pending"}).sort("timestamp", 1)
        return [{
            "id": str(doc["_id"]),
            "filename": doc["filename"],
            "mime_type": doc["mime_type"],
            "submitted_by": doc["submitted_by"],
            "timestamp": doc["timestamp"].isoformat()
        } for doc in cursor]

    def get_approval(self, approval_id: str):
        return self.collection.find_one({"_id": ObjectId(approval_id)})

    def mark_approved(self, approval_id: str):
        self.collection.update_one({"_id": ObjectId(approval_id)}, {"$set": {"status": "approved"}})

    def mark_rejected(self, approval_id: str):
        self.collection.update_one({"_id": ObjectId(approval_id)}, {"$set": {"status": "rejected"}})
        
approval_manager = ApprovalManager()
