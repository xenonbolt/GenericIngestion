import os
import time
from pymongo import MongoClient
from agents.state import AgentState, streamer
from agents.utils import get_metrics

async def ticket_analysis_node(state: AgentState):
    """Queries MongoDB for a specific customer's tickets and aggregates sentiment/escalation metrics."""
    start_time = time.time()
    node_id = "ticket_analysis_node"
    await streamer.emit_node_active(node_id, "Querying historical ticket data...")
    customer_id = state.get("target_customer_id")
    
    if not customer_id:
        state["ticket_analysis"] = "Error: No customer ID provided for ticket analysis."
        return state

    # Connect to MongoDB directly
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["cxo_sentiment_db"]
    tickets_col = db["tickets"]

    # Fetch tickets
    tickets = list(tickets_col.find({"customer_id": customer_id}))
    
    if not tickets:
        state["ticket_analysis"] = f"No tickets found for customer {customer_id}."
        return state
        
    total_tickets = len(tickets)
    escalated_count = 0
    sla_breaches = 0
    
    sentiment_counts = {
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0,
        "Frustrated": 0
    }
    
    recent_summaries = []

    for t in tickets:
        status = t.get("status", "")
        if status.lower() == "escalated" or t.get("escalation_details"):
            escalated_count += 1
            
        if t.get("sla_breach"):
            sla_breaches += 1
            
        ai_analysis = t.get("ai_analysis", {})
        sentiment = ai_analysis.get("sentiment_score", "Neutral")
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        summary = ai_analysis.get("summary")
        if summary:
            recent_summaries.append(f"- Ticket {t.get('ticket_id')}: {summary} (Sentiment: {sentiment})")

    analysis_report = f"### Ticket History Analysis for {customer_id}\n"
    analysis_report += f"**Total Tickets:** {total_tickets}\n"
    analysis_report += f"**Escalated Tickets:** {escalated_count}\n"
    analysis_report += f"**SLA Breaches:** {sla_breaches}\n"
    analysis_report += f"**Sentiment Breakdown:** {sentiment_counts}\n\n"
    analysis_report += "**Recent Summaries:**\n" + "\n".join(recent_summaries[:5]) # Limit to top 5
    
    state["ticket_analysis"] = analysis_report
    
    await streamer.emit_node_completed(node_id, get_metrics(start_time))
    return state
