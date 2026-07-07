from pymongo import MongoClient
import uuid

class UserManager:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "agentic_platform"):
        self.client = MongoClient(uri)
        self.collection = self.client[db_name]["users"]
        
        # Bootstrap admin user if it doesn't exist
        if not self.collection.find_one({"username": "admin"}):
            self.collection.insert_one({"username": "admin", "password": "password", "role": "admin"})

    def signup(self, username, password):
        if self.collection.find_one({"username": username}):
            return {"error": "Username already exists"}
        
        # In a real system, password should be hashed.
        role = "admin" if username == "admin" else "basic"
        self.collection.insert_one({
            "username": username,
            "password": password,
            "role": role
        })
        return {"success": True, "role": role}

    def create_user(self, username: str, password: str, role: str):
        """Create a user with an explicitly specified role (admin-only action)."""
        if self.collection.find_one({"username": username}):
            return {"error": "Username already exists"}
        self.collection.insert_one({
            "username": username,
            "password": password,
            "role": role
        })
        return {"success": True, "role": role}

    def login(self, username, password):
        # We allow password="admin" to override for ease of testing based on user prompt,
        # otherwise verify normal password.
        user = self.collection.find_one({"username": username})
        if not user:
            return None
        
        if username == "admin" and password == "admin":
            pass # Hardcoded bootstrap override as requested
        elif user.get("password") != password:
            return None
            
        token = str(uuid.uuid4()) # Mock session token
        return {"username": user["username"], "role": user["role"], "token": token}

    def get_all_users(self):
        cursor = self.collection.find()
        return [{"username": doc["username"], "role": doc["role"]} for doc in cursor]
        
    def update_user_role(self, username: str, new_role: str):
        result = self.collection.update_one({"username": username}, {"$set": {"role": new_role}})
        return result.modified_count > 0

user_manager = UserManager()
