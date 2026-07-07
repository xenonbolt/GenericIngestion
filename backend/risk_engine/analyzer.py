import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

def get_llm():
    llm_provider = os.getenv("LLM_PROVIDER", "google").lower()
    if llm_provider == "openai":
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        llm_kwargs = {"model": model_name, "temperature": 0.1}
        headroom_proxy = os.getenv("HEADROOM_PROXY")
        if headroom_proxy:
            llm_kwargs["base_url"] = headroom_proxy
        return ChatOpenAI(**llm_kwargs)
    else:
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.1)

SYSTEM_PROMPT = """
You are an advanced Customer Success Risk Analyzer. 
You will be provided with customer interaction data (tickets, emails, transcripts).
Analyze the data and return a JSON object with the following schema:
{
    "sentiment": "Strongly Positive | Positive | Neutral | Negative | Strongly Negative",
    "emotion": "Frustrated | Angry | Confused | Disappointed | Anxious | Urgent | Disengaged | Satisfied",
    "complaint_themes": ["SLA breach", "Repeated issue", "Poor resolution", "Product defect", "Billing issue", "Communication gap", "Handoff frustration", "Executive concern", "Renewal concern", "Churn intent"],
    "signals": {
        "sla_breach_count": <int>,
        "ticket_reopen_count": <int>,
        "repeated_issue": <boolean>,
        "handoff_occurred": <boolean>,
        "executive_involved": <boolean>,
        "churn_intent_expressed": <boolean>,
        "renewal_due_soon": <boolean>,
        "loss_of_confidence": <boolean>
    },
    "root_cause_summary": "<A concise GenAI executive summary of the root cause of the customer's issues and overall situation>"
}
IMPORTANT: Return ONLY valid JSON. Do not include markdown formatting like ```json or extra text.
"""

def calculate_risk_score(signals, sentiment):
    # Default weights totaling 100
    weights = {
        "sentiment_trend": 15,
        "complaint_severity": 10,
        "sla_breach": 15,
        "ticket_reopen": 10,
        "repeated_issue": 10,
        "handoff": 5,
        "executive_involvement": 15,
        "churn_intent": 10,
        "renewal_proximity": 10
    }
    
    score = 0
    if sentiment in ["Negative", "Strongly Negative"]:
        score += weights["sentiment_trend"]
    if signals.get("loss_of_confidence", False):
        score += weights["complaint_severity"]
    if signals.get("sla_breach_count", 0) > 0:
        score += weights["sla_breach"]
    if signals.get("ticket_reopen_count", 0) > 0:
        score += weights["ticket_reopen"]
    if signals.get("repeated_issue", False):
        score += weights["repeated_issue"]
    if signals.get("handoff_occurred", False):
        score += weights["handoff"]
    if signals.get("executive_involved", False):
        score += weights["executive_involvement"]
    if signals.get("churn_intent_expressed", False):
        score += weights["churn_intent"]
    if signals.get("renewal_due_soon", False):
        score += weights["renewal_proximity"]
        
    risk_level = "Low"
    if score >= 86:
        risk_level = "Critical"
    elif score >= 71:
        risk_level = "High"
    elif score >= 41:
        risk_level = "Medium"
        
    return {"score": score, "level": risk_level}

def get_next_best_action(risk_level):
    actions = {
        "Low": ["Continue standard support"],
        "Medium": ["Assign dedicated engineer", "Provide clear ETA"],
        "High": ["Prioritize ticket", "Assign experienced agent"],
        "Critical": ["Trigger leadership review", "Service recovery playbook", "Schedule executive business review"]
    }
    return actions.get(risk_level, [])

async def analyze_risk(text_data: str) -> dict:
    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Data:\n{text_data}")
    ]
    
    try:
        result = await llm.ainvoke(messages)
        content = result.content.strip()
        
        # Clean markdown formatting if model didn't follow instructions
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        analysis = json.loads(content.strip())
        
        signals = analysis.get("signals", {})
        sentiment = analysis.get("sentiment", "Neutral")
        
        risk_calc = calculate_risk_score(signals, sentiment)
        next_best_action = get_next_best_action(risk_calc["level"])
        
        return {
            "analysis": analysis,
            "risk_score": risk_calc["score"],
            "risk_level": risk_calc["level"],
            "next_best_action": next_best_action
        }
    except Exception as e:
        raise Exception(f"Failed to analyze risk: {str(e)}")
