import os
import json
import glob
import traceback
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

class SignalsOutput(BaseModel):
    sla_breach_count: int = 0
    ticket_reopen_count: int = 0
    repeated_issue: bool = False
    handoff_occurred: bool = False
    executive_involved: bool = False
    churn_intent_expressed: bool = False
    renewal_due_soon: bool = False
    loss_of_confidence: bool = False

class TicketRiskAnalysisOutput(BaseModel):
    sentiment: str = Field(description="Strongly Positive | Positive | Neutral | Negative | Strongly Negative")
    emotion: str = Field(description="Frustrated | Angry | Confused | Disappointed | Anxious | Urgent | Disengaged | Satisfied")
    complaint_themes: list[str] = Field(description="List of themes like 'SLA breach', 'Repeated issue', etc.")
    signals: SignalsOutput
    root_cause_summary: str = Field(description="A concise GenAI executive summary of the root cause of the customer's issues and overall situation")

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
    if getattr(signals, "loss_of_confidence", False):
        score += weights["complaint_severity"]
    if getattr(signals, "sla_breach_count", 0) > 0:
        score += weights["sla_breach"]
    if getattr(signals, "ticket_reopen_count", 0) > 0:
        score += weights["ticket_reopen"]
    if getattr(signals, "repeated_issue", False):
        score += weights["repeated_issue"]
    if getattr(signals, "handoff_occurred", False):
        score += weights["handoff"]
    if getattr(signals, "executive_involved", False):
        score += weights["executive_involvement"]
    if getattr(signals, "churn_intent_expressed", False):
        score += weights["churn_intent"]
    if getattr(signals, "renewal_due_soon", False):
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

class CustomerDataPipeline:
    def __init__(self):
        # Initialize MongoDB
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client["cxo_sentiment_db"]
        self.customers_col = self.db["customers"]
        self.tickets_col = self.db["tickets"]
        
        # Ensure indexes
        self.customers_col.create_index("_id")
        self.tickets_col.create_index("_id")
        
        # Initialize LLM
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if self.llm_provider == "openai":
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
            llm_kwargs = {"model": model_name, "temperature": 0.2}
            headroom_proxy = os.getenv("HEADROOM_PROXY")
            if headroom_proxy:
                llm_kwargs["base_url"] = headroom_proxy
            self.llm = ChatOpenAI(**llm_kwargs).with_structured_output(TicketRiskAnalysisOutput)
        else:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2).with_structured_output(TicketRiskAnalysisOutput)

    def ingest_dataset(self, dataset_path: str):
        """Main entry point to ingest the customer support dataset from a flat directory structure."""
        print(f"Starting ingestion from dataset path: {dataset_path}")
        
        # Look recursively for all JSON files
        pattern = os.path.join(dataset_path, "**", "*.json")
        all_json_files = glob.glob(pattern, recursive=True)
        
        print(f"Found {len(all_json_files)} JSON files. Categorizing...")
        
        # Separate base tickets from escalation details
        ticket_files = []
        escalation_files = {}
        
        for file_path in all_json_files:
            if "EscalationDetails" in file_path:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "ticket_id" in data:
                            escalation_files[data["ticket_id"]] = data
                except Exception as e:
                    print(f"Failed to read escalation file {file_path}: {e}")
            else:
                ticket_files.append(file_path)
        
        print(f"Processing {len(ticket_files)} tickets and found {len(escalation_files)} escalations.")

        for file_path in ticket_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    ticket_data = json.load(f)
                    
                ticket_id = ticket_data.get("ticket_id")
                customer_id = ticket_data.get("customer_id")
                
                if not ticket_id or not customer_id:
                    continue
                
                # 1. Mock and Upsert Customer Data
                mock_customer = {
                    "_id": customer_id,
                    "customer_id": customer_id,
                    "customer_name": f"Mock Customer {customer_id.replace('CUST', '')}",
                    "account_type": "Enterprise" if int(customer_id.replace('CUST', '') or 0) % 2 == 0 else "Premium"
                }
                self.customers_col.replace_one({"_id": customer_id}, mock_customer, upsert=True)
                
                # Assign primary key for ticket
                ticket_data["_id"] = ticket_id
                
                # 2. Merge Escalation Details if present
                if ticket_id in escalation_files:
                    escalation_data = escalation_files[ticket_id]
                    ticket_data["escalation_details"] = {
                        "escalation_date": escalation_data.get("escalation_date"),
                        "final_resolution": escalation_data.get("final_resolution", {})
                    }
                
                # 3. Process Sentiment & Summary
                comment_history = ticket_data.get("comment_history", [])
                if comment_history:
                    # Build conversation text (handle different structures e.g. "text" vs "comment")
                    conversation_text = ""
                    for msg in comment_history:
                        author = str(msg.get("author", "unknown")).upper()
                        text = str(msg.get("comment", msg.get("text", "")))
                        conversation_text += f"{author}: {text}\n"
                    
                    # Call LLM
                    try:
                        prompt_template = f"""You are an advanced Customer Success Risk Analyzer. 
You will be provided with customer interaction data (tickets, emails, transcripts).
Analyze the data and extract the appropriate risk signals and summaries to fill the requested schema.

Guidelines for fields:
- sentiment: Strongly Positive | Positive | Neutral | Negative | Strongly Negative
- emotion: Frustrated | Angry | Confused | Disappointed | Anxious | Urgent | Disengaged | Satisfied
- complaint_themes: Pick from ["SLA breach", "Repeated issue", "Poor resolution", "Product defect", "Billing issue", "Communication gap", "Handoff frustration", "Executive concern", "Renewal concern", "Churn intent"]
- root_cause_summary: A concise GenAI executive summary of the root cause of the customer's issues and overall situation. YOU MUST PROVIDE THIS. DO NOT LEAVE EMPTY.

Conversation:
\"\"\"
{conversation_text}
\"\"\"
"""
                        print(f"[INFO] Calling LLM for ticket {ticket_id}...")
                        ai_result = self.llm.invoke(prompt_template)
                        print(f"[INFO] LLM result type: {type(ai_result)}, value: {ai_result}")
                        
                        # Handle both dict and Pydantic model responses
                        if isinstance(ai_result, dict):
                            sentiment = ai_result.get("sentiment", "") or "Neutral"
                            emotion = ai_result.get("emotion", "") or "Neutral"
                            themes = ai_result.get("complaint_themes", None) or []
                            signals_dict = ai_result.get("signals", {})
                            root_cause = ai_result.get("root_cause_summary", "") or "No root cause summary generated."
                            # Build a mock signals object for calculate_risk_score
                            class _Sig:
                                def __init__(self, d): self.__dict__.update(d)
                                def model_dump(self): return self.__dict__
                            signals = _Sig(signals_dict) if signals_dict else None
                        else:
                            sentiment = getattr(ai_result, "sentiment", "") or "Neutral"
                            emotion = getattr(ai_result, "emotion", "") or "Neutral"
                            themes = getattr(ai_result, "complaint_themes", None) or []
                            signals = getattr(ai_result, "signals", None)
                            root_cause = getattr(ai_result, "root_cause_summary", "") or "No root cause summary generated."
                        
                        risk_calc = calculate_risk_score(signals, sentiment)
                        next_best_action = get_next_best_action(risk_calc["level"])
                        
                        ticket_data["ai_analysis"] = {
                            "sentiment": sentiment,
                            "emotion": emotion,
                            "complaint_themes": themes,
                            "signals": signals.model_dump() if signals else {},
                            "root_cause_summary": root_cause,
                            "risk_score": risk_calc["score"],
                            "risk_level": risk_calc["level"],
                            "next_best_action": next_best_action
                        }
                    except Exception as llm_err:
                        print(f"[ERROR] LLM extraction failed for {ticket_id}: {llm_err}")
                        traceback.print_exc()
                        ticket_data["ai_analysis"] = {
                            "sentiment": "Neutral",
                            "emotion": "Neutral",
                            "complaint_themes": [],
                            "signals": {},
                            "root_cause_summary": "Analysis failed",
                            "risk_score": 0,
                            "risk_level": "Low",
                            "next_best_action": []
                        }
                else:
                    ticket_data["ai_analysis"] = {
                        "sentiment": "Neutral",
                        "emotion": "Neutral",
                        "complaint_themes": [],
                        "signals": {},
                        "root_cause_summary": "No comments available",
                        "risk_score": 0,
                        "risk_level": "Low",
                        "next_best_action": []
                    }
                    
                # 4. Insert / Upsert Ticket
                self.tickets_col.replace_one({"_id": ticket_id}, ticket_data, upsert=True)
                print(f"Ingested ticket: {ticket_id} for customer {customer_id}")
                
            except Exception as e:
                print(f"Failed to process ticket file {file_path}: {e}")
                
        print("Dataset ingestion complete.")

pipeline = CustomerDataPipeline()
