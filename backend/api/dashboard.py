from fastapi import APIRouter, HTTPException, BackgroundTasks
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime, timezone
import os
import uuid

router = APIRouter()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["cxo_sentiment_db"]
customers_col = db["customers"]
escalations_col = db["escalation_requests"]

@router.get("/customers")
async def get_customers():
    try:
        customers = list(customers_col.find({}))
        return {"status": "success", "customers": customers}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class EscalationRequest(BaseModel):
    customer_id: str
    customer_name: str
    summary: str
    root_cause_analysis: str
    next_best_actions: list[str]


@router.post("/escalations")
async def create_escalation_request(request: EscalationRequest):
    try:
        ticket_number = f"ESC-{uuid.uuid4().hex[:6].upper()}"
        formatted_actions = [
            {"action": action, "actionable_work_items": ""}
            for action in request.next_best_actions
        ]

        doc = {
            "_id": ticket_number,
            "ticket_number": ticket_number,
            "customer_id": request.customer_id,
            "customer_name": request.customer_name,
            "summary": request.summary,
            "root_cause_analysis": request.root_cause_analysis,
            "next_best_actions": formatted_actions,
            "customer_feedback": "",
            "status": "Open",
            "created_date": datetime.now(timezone.utc).isoformat(),
        }

        escalations_col.insert_one(doc)
        return {"status": "success", "ticket_number": ticket_number}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/escalations")
async def get_escalation_requests():
    try:
        tickets = list(escalations_col.find({}))
        return {"status": "success", "tickets": tickets}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class ResolveRequest(BaseModel):
    next_best_actions: list[dict]  # [{action, actionable_work_items}]
    customer_feedback: str


@router.put("/escalations/{ticket_number}/resolve")
async def resolve_escalation(ticket_number: str, body: ResolveRequest, background_tasks: BackgroundTasks):
    # Validate mandatory fields
    for item in body.next_best_actions:
        if not item.get("actionable_work_items", "").strip():
            raise HTTPException(status_code=400, detail=f"Actionable work item is required for action: {item.get('action')}")
    if not body.customer_feedback.strip():
        raise HTTPException(status_code=400, detail="Customer feedback is required.")

    ticket = escalations_col.find_one({"_id": ticket_number})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    escalations_col.update_one(
        {"_id": ticket_number},
        {"$set": {
            "next_best_actions": body.next_best_actions,
            "customer_feedback": body.customer_feedback,
            "status": "Resolved",
            "resolved_date": datetime.now(timezone.utc).isoformat(),
        }}
    )

    # Trigger incremental re-analysis in the background
    customer_id = ticket.get("customer_id")
    if customer_id:
        background_tasks.add_task(
            _run_incremental_analysis,
            customer_id,
            body.next_best_actions,
            body.customer_feedback
        )

    return {"status": "success", "message": f"Ticket {ticket_number} resolved. Re-analysis scheduled."}


def _run_incremental_analysis(customer_id: str, next_best_actions: list, customer_feedback: str):
    """Background task: trigger incremental customer risk profile update."""
    try:
        from ingestion.customer_data_pipeline import pipeline
        pipeline.incremental_update_customer(customer_id, next_best_actions, customer_feedback)
    except Exception as e:
        print(f"[ERROR] Incremental analysis failed for {customer_id}: {e}")
