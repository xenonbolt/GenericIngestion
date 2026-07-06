import os
import json
import uuid
import logging
from pymongo import MongoClient

logger = logging.getLogger("UserManager")

class UserManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "agentic_platform"):
        self.use_fallback = False
        self.fallback_dir = os.path.join(os.getcwd(), "data", "fallback_db")
        os.makedirs(self.fallback_dir, exist_ok=True)
        self.users_path = os.path.join(self.fallback_dir, "users.json")
        
        try:
            logger.info("Connecting to MongoDB for User Manager...")
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            
            self.collection = self.client[db_name]["users"]
            
            # Bootstrap admin user if it doesn't exist
            if not self.collection.find_one({"username": "admin"}):
                self.collection.insert_one({"username": "admin", "password": "password", "role": "admin"})
            logger.info("User Manager connected to MongoDB successfully.")
        except Exception as e:
            logger.warning(f"MongoDB connection failed for User Manager: {e}. Using local JSON database fallback.")
            self.use_fallback = True
            self._init_fallback()

    def _init_fallback(self):
        if not os.path.exists(self.users_path):
            # Bootstrap with admin user
            admin_user = {
                "username": "admin",
                "password": "password",
                "role": "admin"
            }
            with open(self.users_path, "w") as f:
                json.dump([admin_user], f, indent=2)

    def _read_fallback(self) -> list:
        try:
            with open(self.users_path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_fallback(self, data: list):
        try:
            with open(self.users_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write fallback users: {e}")

    def signup(self, username, password):
        if self.use_fallback:
            users = self._read_fallback()
            if any(u["username"] == username for u in users):
                return {"error": "Username already exists"}
            
            role = "admin" if username == "admin" else "basic"
            new_user = {
                "username": username,
                "password": password,
                "role": role
            }
            users.append(new_user)
            self._write_fallback(users)
            return {"success": True, "role": role}

        if self.collection.find_one({"username": username}):
            return {"error": "Username already exists"}
        
        role = "admin" if username == "admin" else "basic"
        self.collection.insert_one({
            "username": username,
            "password": password,
            "role": role
        })
        return {"success": True, "role": role}

    def login(self, username, password):
        if self.use_fallback:
            users = self._read_fallback()
            user = next((u for u in users if u["username"] == username), None)
            if not user:
                return None
            
            # Allow password="admin" override for admin user
            if username == "admin" and password == "admin":
                pass
            elif user.get("password") != password:
                return None
                
            token = str(uuid.uuid4())
            return {"username": user["username"], "role": user["role"], "token": token}

        user = self.collection.find_one({"username": username})
        if not user:
            return None
        
        if username == "admin" and password == "admin":
            pass
        elif user.get("password") != password:
            return None
            
        token = str(uuid.uuid4())
        return {"username": user["username"], "role": user["role"], "token": token}

    def get_all_users(self):
        if self.use_fallback:
            users = self._read_fallback()
            return [{"username": u["username"], "role": u["role"]} for u in users]

        cursor = self.collection.find()
        return [{"username": doc["username"], "role": doc["role"]} for doc in cursor]
        
    def update_user_role(self, username: str, new_role: str):
        if self.use_fallback:
            users = self._read_fallback()
            updated = False
            for u in users:
                if u["username"] == username:
                    if u["role"] != new_role:
                        u["role"] = new_role
                        updated = True
                    break
            if updated:
                self._write_fallback(users)
            return updated

        result = self.collection.update_one({"username": username}, {"$set": {"role": new_role}})
        return result.modified_count > 0

user_manager = UserManager()
