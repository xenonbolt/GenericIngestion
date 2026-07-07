import os
import json
import time
from pymongo import MongoClient
from agents.state import AgentState, streamer
from agents.utils import get_metrics
from langchain_core.messages import AIMessage

async def overall_decision_node(state: AgentState):
    """Fetches the pre-calculated final structured CXO decision from the database."""
    start_time = time.time()
    node_id = "overall_decision_node"
    await streamer.emit_node_active(node_id, "Loading executive risk assessment from database...")
    customer_id = state.get("target_customer_id", "Unknown")
    
    # Query MongoDB for the customer's risk profile
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["cxo_sentiment_db"]
    customers_col = db["customers"]
    
    customer = customers_col.find_one({"_id": customer_id})
    if customer and "risk_profile" in customer:
        risk_profile = customer["risk_profile"]
        risk_profile["customer_id"] = customer_id
        risk_profile["customer_name"] = customer.get("customer_name", customer_id)
        final_json = json.dumps(risk_profile)
    else:
        # Fallback if no profile exists
        fallback = {
            "summary": "No risk profile found in database. Please run ingestion pipeline.",
            "sentiment": "Unknown",
            "escalation_score": 0,
            "root_cause_analysis": "No data available.",
            "complaint_themes": [],
            "next_best_action": [],
            "timeline": "No timeline available.",
            "customer_id": customer_id,
            "customer_name": "Unknown"
        }
        final_json = json.dumps(fallback)
        
    state["messages"].append(AIMessage(content=final_json))
    
    await streamer.emit_node_completed(node_id, get_metrics(start_time))
    return state
