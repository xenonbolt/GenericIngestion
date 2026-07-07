import os
import json
import glob
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

class TicketSentimentOutput(BaseModel):
    summary: str = Field(description="A short, readable summary of the conversation.")
    sentiment_score: str = Field(description="The customer's sentiment. Must be one of: Positive, Neutral, Negative, Frustrated")

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
            self.llm = ChatOpenAI(**llm_kwargs).with_structured_output(TicketSentimentOutput)
        else:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2).with_structured_output(TicketSentimentOutput)

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
                        prompt_template = f"""You are an expert customer support analyst.
Your task is to analyze the following customer support conversation and extract a concise summary and the customer's overall sentiment.

Rules:
1. Provide a short, readable 1-3 sentence summary of the core issue and how it was handled.
2. Determine the customer's sentiment. It MUST be exactly one of: "Positive", "Neutral", "Negative", or "Frustrated".
3. If the conversation is empty, lacks clear sentiment, or you cannot determine it, default the sentiment to "Neutral".

Conversation:
\"\"\"
{conversation_text}
\"\"\"
"""
                        ai_result = self.llm.invoke(prompt_template)
                        if isinstance(ai_result, dict):
                            summary = ai_result.get("summary", "")
                            sentiment = ai_result.get("sentiment_score", "Neutral")
                        else:
                            summary = getattr(ai_result, "summary", "")
                            sentiment = getattr(ai_result, "sentiment_score", "Neutral")
                            
                        ticket_data["ai_analysis"] = {
                            "summary": summary,
                            "sentiment_score": sentiment
                        }
                    except Exception as llm_err:
                        print(f"LLM extraction failed for {ticket_id}: {llm_err}")
                        ticket_data["ai_analysis"] = {
                            "summary": "Analysis failed",
                            "sentiment_score": "Neutral"
                        }
                else:
                    ticket_data["ai_analysis"] = {
                        "summary": "No comments available",
                        "sentiment_score": "Neutral"
                    }
                    
                # 4. Insert / Upsert Ticket
                self.tickets_col.replace_one({"_id": ticket_id}, ticket_data, upsert=True)
                print(f"Ingested ticket: {ticket_id} for customer {customer_id}")
                
            except Exception as e:
                print(f"Failed to process ticket file {file_path}: {e}")
                
        print("Dataset ingestion complete.")

pipeline = CustomerDataPipeline()
