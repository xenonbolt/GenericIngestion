from fastapi import APIRouter
from pymongo import MongoClient
import os

router = APIRouter()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["cxo_sentiment_db"]
customers_col = db["customers"]

@router.get("/customers")
async def get_customers():
    try:
        customers = list(customers_col.find({}))
        # Convert _id to string or remove it if not needed, as it might not be JSON serializable 
        # (though our _id is a string "CUST1001", so it should be fine)
        return {"status": "success", "customers": customers}
    except Exception as e:
        return {"status": "error", "message": str(e)}
