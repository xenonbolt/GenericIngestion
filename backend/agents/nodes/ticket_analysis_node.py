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
    
    risk_level_counts = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0
    }
    
    all_complaint_themes = []
    
    recent_summaries = []

    for t in tickets:
        status = t.get("status", "")
        if status.lower() == "escalated" or t.get("escalation_details"):
            escalated_count += 1
            
        if t.get("sla_breach"):
            sla_breaches += 1
            
        ai_analysis = t.get("ai_analysis", {})
        sentiment = ai_analysis.get("sentiment", "Neutral")
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        risk_level = ai_analysis.get("risk_level", "Low")
        risk_level_counts[risk_level] = risk_level_counts.get(risk_level, 0) + 1
        
        themes = ai_analysis.get("complaint_themes", [])
        if isinstance(themes, list):
            all_complaint_themes.extend(themes)
        
        root_cause = ai_analysis.get("root_cause_summary")
        if root_cause:
            rich_summary = f"- **Ticket {t.get('ticket_id')}** (Sentiment: {sentiment}, Risk: {risk_level})"
            rich_summary += f"\n  - **Root Cause**: {root_cause}"
                 
            nba = ai_analysis.get("next_best_action")
            if nba and isinstance(nba, list):
                 rich_summary += f"\n  - **Next Best Action**: {', '.join(nba)}"
                 
            recent_summaries.append(rich_summary)

    # Aggregate top themes
    from collections import Counter
    theme_counts = Counter(all_complaint_themes).most_common(5)
    top_themes = [f"{theme} ({count})" for theme, count in theme_counts]

    analysis_report = f"### Ticket History Analysis for {customer_id}\n"
    analysis_report += f"**Total Tickets:** {total_tickets}\n"
    analysis_report += f"**Escalated Tickets:** {escalated_count}\n"
    analysis_report += f"**SLA Breaches:** {sla_breaches}\n"
    analysis_report += f"**Sentiment Breakdown:** {sentiment_counts}\n"
    analysis_report += f"**Risk Level Breakdown:** {risk_level_counts}\n"
    if top_themes:
        analysis_report += f"**Top Complaint Themes:** {', '.join(top_themes)}\n"
    analysis_report += "\n**Recent Summaries:**\n" + "\n".join(recent_summaries[:5]) # Limit to top 5
    
    state["ticket_analysis"] = analysis_report
    
    await streamer.emit_node_completed(node_id, get_metrics(start_time))
    return state
