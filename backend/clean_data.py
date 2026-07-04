import shutil
import os
from pymongo import MongoClient

backend_dir = "/home/dwijo/Desktop/QuarterFinal/backend"
dirs_to_remove = [
    os.path.join(backend_dir, "chroma_db"),
    os.path.join(backend_dir, "kuzu_db"),
    os.path.join(backend_dir, "data", "uploads"),
    os.path.join(backend_dir, "temp_uploads"),
]

files_to_remove = [
    os.path.join(backend_dir, "data", "knowledge_graph.gpickle"),
    os.path.join(backend_dir, "data", "ontology.json"),
]

for d in dirs_to_remove:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"Removed directory: {d}")

for f in files_to_remove:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed file: {f}")

try:
    client = MongoClient("mongodb://localhost:27017/")
    client.drop_database("ai_agent_db")
    print("Dropped MongoDB database: ai_agent_db")
except Exception as e:
    print(f"Failed to drop MongoDB: {e}")
