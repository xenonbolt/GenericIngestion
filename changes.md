# Backend Modifications: Risk Analysis & ServiceNow Integration

This document outlines the architectural changes made to the backend to support the Customer Success Risk Analyzer use case, focusing on the ServiceNow API, User Profiles, and the generic Risk Engine.

## 1. ServiceNow API Integration
We built a dedicated endpoint to fetch customer-specific incidents from the ServiceNow instance and automatically generate a unified timeline.

* **File:** [backend/api/snow.py](file:///home/dwijo/Desktop/QuarterFinal/backend/api/snow.py)
* **Endpoint:** `GET /api/snow/timeline/{customer_id}`
* **Functionality:** 
  * Connects to SNOW via Basic Auth (using credentials or environment variables).
  * Queries the `incident` table where `caller_id.user_name` matches the `customer_id`.
  * Extracts essential fields (state, priority, SLA breaches, escalation notes).
  * Uses the LLM to synthesize this raw JSON data into a chronological **Customer Journey Timeline** markdown profile.
  * Triggers the User Manager to save this profile to the database.

## 2. Generic Risk Engine Module
We decoupled the Risk Analysis logic from specific integrations, creating a reusable engine capable of processing any textual data (tickets, emails, transcripts) to extract operational signals.

* **File:** [backend/risk_engine/analyzer.py](file:///home/dwijo/Desktop/QuarterFinal/backend/risk_engine/analyzer.py)
* **Functionality:**
  * **Signal Extraction:** Uses a single, optimized LLM prompt to identify `sentiment`, `emotion`, `complaint_themes`, and critical Boolean signals (e.g., `loss_of_confidence`, `executive_involved`).
  * **Risk Scoring Framework:** Implements the mathematically weighted algorithm defined in the use case to compute a 0-100 `Escalation Risk Score`.
  * **Next Best Action:** Maps the resulting Risk Band (Low/Medium/High/Critical) to recommended recovery actions (e.g., "Service recovery playbook").
  * **Root Cause Summary:** Generates a concise GenAI executive summary of the issue.
* **File:** [backend/api/risk.py](file:///home/dwijo/Desktop/QuarterFinal/backend/api/risk.py)
  * **Endpoint:** `POST /api/risk/analyze`
  * **Functionality:** Exposes the Risk Engine to the frontend, taking a `customer_id` and raw `source_data`, and saving the resulting `risk_profile`.

## 3. User Profile Storage
We expanded the MongoDB-backed User Manager to act as a centralized customer profile repository, persisting the outputs of the new APIs.

* **File:** [backend/auth/user_manager.py](file:///home/dwijo/Desktop/QuarterFinal/backend/auth/user_manager.py)
* **Modifications:**
  * Added `update_user_timeline` and `get_user_timeline` to manage the SNOW-generated chronological view.
  * Added `update_user_risk_profile` and `get_user_risk_profile` to store the calculated risk score, sentiment, themes, and root cause summary.
* **File:** [backend/main.py](file:///home/dwijo/Desktop/QuarterFinal/backend/main.py)
  * Cleaned up the main FastAPI app to register the new `snow_router` and `risk_router`.

---

## Unused / Legacy Files
Based on the current architecture prioritizing sentiment analysis, risk prediction, and data ingestion, the following legacy chatbot and graph components are no longer required for the actual flow and can be safely ignored or removed:

* `backend/agents/` (The entire directory containing LangGraph conversational logic)
* `backend/graph/` (NetworkX and Kuzu stores)
* `backend/api/chat.py` (The conversational chat router)
* `backend/test_agent.py`
