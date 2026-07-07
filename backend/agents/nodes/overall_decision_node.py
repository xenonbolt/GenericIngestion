import os
import json
import time
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from agents.state import AgentState, streamer
from agents.utils import get_metrics

class FinalDecision(BaseModel):
    summary: str = Field(description="A brief 2-3 sentence overall summary of the customer's current standing.")
    sentiment: str = Field(description="Overall Customer Sentiment (e.g., Positive, Neutral, Negative, Frustrated).")
    escalation_score: int = Field(description="Escalation Prediction Score as a percentage (0 to 100).")
    reasoning: str = Field(description="Brief explanation for the score.")

async def overall_decision_node(state: AgentState):
    """Combines ticket analysis and transcript analysis to form a final structured CXO decision."""
    start_time = time.time()
    node_id = "overall_decision_node"
    await streamer.emit_node_active(node_id, "Synthesizing executive risk assessment...")
    customer_id = state.get("target_customer_id", "Unknown")
    
    ticket_analysis = state.get("ticket_analysis", "No ticket data.")
    transcript_analysis = state.get("transcript_analysis", "No transcript data.")
    
    prompt = f"""You are an Executive AI Analyst for a Customer Experience Officer (CXO) dashboard.
Your task is to review the aggregated data for customer {customer_id} and provide an executive risk assessment.

Data Sources:
--- TICKET HISTORY ANALYSIS ---
{ticket_analysis}

--- EXTERNAL TRANSCRIPT ANALYSIS ---
{transcript_analysis}
"""

    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if llm_provider == "openai":
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        llm_kwargs = {"model": model_name, "temperature": 0.2}
        headroom_proxy = os.getenv("HEADROOM_PROXY")
        if headroom_proxy:
            llm_kwargs["base_url"] = headroom_proxy
        llm = ChatOpenAI(**llm_kwargs).with_structured_output(FinalDecision, include_raw=True)
    else:
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2).with_structured_output(FinalDecision, include_raw=True)
        
    # Run structured generation
    resp = await llm.ainvoke(prompt)
    
    parsed_obj = resp["parsed"]
    raw_msg = resp["raw"]
    
    # Convert Pydantic model to dict
    if isinstance(parsed_obj, dict):
        final_json = json.dumps(parsed_obj)
    else:
        final_json = parsed_obj.model_dump_json()
    
    # Add back to state (as a system/assistant message or similar)
    from langchain_core.messages import AIMessage
    state["messages"].append(AIMessage(content=final_json))
    
    await streamer.emit_node_completed(node_id, get_metrics(start_time, raw_msg))
    return state
