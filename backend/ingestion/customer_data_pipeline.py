import os
import json
import glob
import traceback
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from telemetry import setup_telemetry
setup_telemetry()

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

class CustomerRiskProfile(BaseModel):
    timeline: str = Field(description="Markdown formatted Customer Journey Timeline")
    summary: str = Field(description="A brief 2-3 sentence overall summary of the customer's current standing.")
    sentiment: str = Field(description="Overall Customer Sentiment (e.g., Positive, Neutral, Negative, Frustrated).")
    escalation_score: int = Field(description="Escalation Prediction Score as a percentage (0 to 100).")
    root_cause_analysis: str = Field(description="A detailed analysis of the root causes of the customer's issues based on ticket history.")
    complaint_themes: list[str] = Field(description="List of top complaint themes extracted from the historical data.", default_factory=list)
    next_best_action: list[str] = Field(description="Recommended actionable next steps for the CXO or support team.", default_factory=list)

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
            self.llm_customer = ChatOpenAI(**llm_kwargs).with_structured_output(CustomerRiskProfile)
        else:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2).with_structured_output(TicketRiskAnalysisOutput)
            self.llm_customer = ChatGoogleGenerativeAI(model=model_name, temperature=0.2).with_structured_output(CustomerRiskProfile)

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

        customer_tickets_map = {}

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
                
                if customer_id not in customer_tickets_map:
                    customer_tickets_map[customer_id] = []
                customer_tickets_map[customer_id].append(ticket_data)
                
            except Exception as e:
                print(f"Failed to process ticket file {file_path}: {e}")
                
        # Phase 2: Holistic Customer Analysis & Timeline Generation
        print("Starting Phase 2: Holistic Customer Analysis...")
        for customer_id, tickets in customer_tickets_map.items():
            filtered = []
            for t in tickets:
                filtered.append({
                    "ticket_id": t.get("ticket_id"),
                    "created_date": t.get("created_date"),
                    "status": t.get("status"),
                    "priority": t.get("priority"),
                    "category": t.get("category"),
                    "sla_breach": t.get("sla_breach"),
                    "comment_history": t.get("comment_history")
                })
            
            prompt = f"""You are an Executive AI Analyst for a Customer Experience Officer (CXO).
Analyze the following raw ticket history for Customer {customer_id} and generate a comprehensive Customer Risk Profile.

You are an AI assistant that analyzes customer service tickets and generates a customer journey timeline. 
Your task is to take the raw JSON data of ServiceNow incidents (or similar ticket systems) and convert it into a timeline as follows:

**Example Timeline:**
* **Customer:** {customer_id}
* **Day 1 (YYYY-MM-DD):** <Aggregate Event description for this day> [Overall Sentiment: <Sentiment>]
* **Day X (YYYY-MM-DD):** <Aggregate Event description for this day> [Overall Sentiment: <Sentiment>]
* **Current Status:** <status>

Look for SLA breaches, sentiment changes, repeated issues, escalations, and resolved tickets to build a coherent timeline. 
CRITICAL RULES FOR TIMELINE:
1. You must group ALL events that occur on the SAME DAY into a SINGLE timeline entry for that day. 
2. Do NOT create multiple entries for the same day (e.g., do not output Day 1 multiple times).
3. For each day with an entry, you MUST determine and append a single overall sentiment for that entire day in the exact format: [Overall Sentiment: <Sentiment>].
Raw Tickets:
{json.dumps(filtered, indent=2)}
"""
            print(f"Generating holistic profile for {customer_id}...")
            try:
                profile_obj = self.llm_customer.invoke(prompt)
                
                if isinstance(profile_obj, dict):
                    profile_dict = profile_obj
                else:
                    profile_dict = profile_obj.model_dump()
                    
                self.customers_col.update_one(
                    {"_id": customer_id},
                    {"$set": {"risk_profile": profile_dict}}
                )
                print(f"Successfully generated profile for {customer_id}")
            except Exception as e:
                print(f"Failed to generate holistic profile for {customer_id}: {e}")
                traceback.print_exc()

        print("Dataset ingestion complete.")

    def incremental_update_customer(self, customer_id: str, resolved_actions: list, customer_feedback: str):
        """Incrementally update a customer's risk profile using existing profile + resolution data.
        
        Instead of re-processing all historical tickets, this feeds the LLM the current
        Customer Journey Timeline, Sentiment, Escalation Risk, and Next Best Actions as
        a knowledge base, then applies the newly resolved actions and customer feedback
        as an incremental update to generate a refreshed profile.
        """
        print(f"[INCREMENTAL] Starting incremental update for {customer_id}...")
        customer = self.customers_col.find_one({"_id": customer_id})
        if not customer or "risk_profile" not in customer:
            print(f"[INCREMENTAL] No existing profile found for {customer_id}. Skipping.")
            return

        existing_profile = customer["risk_profile"]
        existing_timeline = existing_profile.get("timeline", "No timeline available.")
        existing_sentiment = existing_profile.get("sentiment", "Unknown")
        existing_escalation_score = existing_profile.get("escalation_score", 0)
        existing_next_best_actions = existing_profile.get("next_best_action", [])

        # Format resolved actions for the prompt
        resolved_summary = "\n".join([
            f"  - Action: {item.get('action', '')}\n    Work Done: {item.get('actionable_work_items', '')}"
            for item in resolved_actions
        ])

        prompt = f"""You are an Executive AI Analyst for a Customer Experience Officer (CXO).

An escalation ticket for Customer {customer_id} has been RESOLVED. Your task is to update the customer's risk profile incrementally based on the resolution data below.

**EXISTING CUSTOMER STATE (your knowledge base):**
- Current Sentiment: {existing_sentiment}
- Current Escalation Risk Score: {existing_escalation_score}%
- Current Next Best Actions: {existing_next_best_actions}
- Current Journey Timeline:
{existing_timeline}

**NEW RESOLUTION DATA (incremental update):**
- Resolved Actions & Work Done:
{resolved_summary}

- Customer Feedback Post-Resolution:
  "{customer_feedback}"

**YOUR TASK:**
Using the existing state as context, generate an UPDATED Customer Risk Profile that reflects the resolution. 
Add a new entry to the timeline (using today's date) to capture this resolution event and the customer feedback.
Re-evaluate the Overall Sentiment and Escalation Risk Score based on whether the actions taken and customer feedback are positive indicators.
If the customer feedback is positive and issues are resolved, the risk score should decrease accordingly.
Keep the timeline format consistent:
* **Day N (YYYY-MM-DD):** <Event description> [Overall Sentiment: <Sentiment>]

Generate the complete updated profile including the refreshed timeline, updated sentiment, updated escalation score, root cause analysis, complaint themes, and next best actions.
"""
        try:
            print(f"[INCREMENTAL] Calling LLM for incremental update of {customer_id}...")
            profile_obj = self.llm_customer.invoke(prompt)

            if isinstance(profile_obj, dict):
                profile_dict = profile_obj
            else:
                profile_dict = profile_obj.model_dump()

            self.customers_col.update_one(
                {"_id": customer_id},
                {"$set": {"risk_profile": profile_dict}}
            )
            print(f"[INCREMENTAL] Successfully updated profile for {customer_id}.")
        except Exception as e:
            print(f"[INCREMENTAL] Failed to update profile for {customer_id}: {e}")
            traceback.print_exc()


pipeline = CustomerDataPipeline()
