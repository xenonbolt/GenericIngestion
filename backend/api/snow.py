import os
import requests
from fastapi import APIRouter, HTTPException
from requests.auth import HTTPBasicAuth
from auth.user_manager import user_manager
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter(prefix="/api/snow")

def get_llm():
    llm_provider = os.getenv("LLM_PROVIDER", "google").lower()
    if llm_provider == "openai":
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        llm_kwargs = {"model": model_name, "temperature": 0.2}
        headroom_proxy = os.getenv("HEADROOM_PROXY")
        if headroom_proxy:
            llm_kwargs["base_url"] = headroom_proxy
        return ChatOpenAI(**llm_kwargs)
    else:
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.2)

@router.get("/timeline/{customer_id}")
async def get_customer_timeline(customer_id: str):
    # Fetch data from SNOW
    # Provide the credentials. Using env variables with defaults.
    snow_url = os.getenv("SNOW_URL", "https://dev420378.service-now.com/api/now/table/incident")
    snow_user = os.getenv("SNOW_USER", "admin")
    snow_pass = os.getenv("SNOW_PASSWORD", "pzZ5*oRMi3=N")
    
    # Query incidents for this caller
    # The user asked to use caller_id.user_name = customer_id
    query_url = f"{snow_url}?sysparm_query=caller_id.user_name={customer_id}&sysparm_display_value=true"
    
    try:
        response = requests.get(query_url, auth=HTTPBasicAuth(snow_user, snow_pass), headers={"Accept": "application/json"}, timeout=15)
        response.raise_for_status()
        data = response.json()
        records = data.get("result", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from ServiceNow: {str(e)}")

    if not records:
        # Default empty timeline message or error
        return {"status": "success", "message": "No records found for this customer.", "timeline": ""}
        
    # Prepare the prompt
    system_prompt = (
        "You are an AI assistant that analyzes customer service tickets and generates a customer journey timeline. "
        "Your task is to take the raw JSON data of ServiceNow incidents and convert it into a timeline as follows:\n\n"
        "**Example Timeline:**\n"
        "* **Customer:** <customer_id>\n"
        "* **Account Type:** <derive if possible, else Default>\n"
        "* **Renewal Due:** <derive if possible, else Unknown>\n"
        "* **Day 1:** <Event description>\n"
        "* **Day X:** <Event description>\n"
        "* **Current Status:** <status>\n\n"
        "Look for SLA breaches, sentiment changes, repeated issues, escalations, and resolved tickets to build a coherent timeline."
    )
    
    # Send only relevant fields to avoid token limits
    filtered_records = []
    for r in records:
        filtered_records.append({
            "number": r.get("number"),
            "opened_at": r.get("opened_at"),
            "resolved_at": r.get("resolved_at"),
            "short_description": r.get("short_description"),
            "description": r.get("description"),
            "state": r.get("state"),
            "priority": r.get("priority"),
            "made_sla": r.get("made_sla"),
            "escalation": r.get("escalation"),
            "comments_and_work_notes": r.get("comments_and_work_notes")
        })

    user_prompt = f"Customer ID: {customer_id}\n\nHere are the raw JSON incidents:\n{json.dumps(filtered_records, indent=2)}\n\nPlease generate the timeline."
    
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        result = await llm.ainvoke(messages)
        timeline = result.content
        
        # Save to user manager
        user_manager.update_user_timeline(customer_id, timeline)
        
        return {"status": "success", "timeline": timeline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate timeline: {str(e)}")
