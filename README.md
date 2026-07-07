# Universal Customer Intelligence & Escalation Platform

Welcome to the **Universal Customer Intelligence Platform**! 

This project is a powerful AI-driven application designed to analyze customer support tickets, automatically generate holistic customer journey timelines, and proactively manage churn through automated Escalation Risk scoring and dedicated Risk Manager workflows.

---

## ✨ Features at a Glance

1. **AI-Driven Customer Profiling**: Upload raw customer service tickets (JSON) and let the AI generate a chronological Journey Timeline, complete with Root Cause Analysis and dynamic sentiment tracking.
2. **Customer Delight Dashboard**: A real-time tabular matrix displaying all customers and their computed Escalation Risk score.
3. **Automated Escalation Triggers**: Customers with a risk score > 50% automatically trigger a workflow allowing agents to request a dedicated Risk Manager.
4. **Risk Manager Workflow**: A dedicated, role-based dashboard where Risk Managers can review escalations, document actionable work items against AI-recommended next best actions, and log customer feedback.
5. **Incremental AI Re-Analysis**: Upon resolving a ticket, the AI incrementally updates the customer's profile and lowers the risk score without needing to expensively re-process historical data.

---

## 🛠 Prerequisites

1. **Python 3.10+**: [Download Python here](https://www.python.org/downloads/). Runs the AI ingestion and backend APIs.
2. **Node.js (version 18+)**: [Download Node.js here](https://nodejs.org/). Runs the React frontend dashboard.
3. **MongoDB**: Stores customer profiles, timelines, and escalation tickets.
   - *Linux (Ubuntu)*: `sudo apt install mongodb`
   - *Windows/Mac*: Download [MongoDB Community Server](https://www.mongodb.com/try/download/community).

---

## 🚀 Step-by-Step Setup Guide

### Step 1: Configure Environment Variables (.env)
1. Navigate into the `backend` folder.
2. Open the file named `.env` (create it if it doesn't exist).
3. Add your AI API key:

```env
# Which AI provider to use: 'google' (Gemini) or 'openai' (GPT)
LLM_PROVIDER="google"

# Your API Keys
GEMINI_API_KEY="your-gemini-key-here"
OPENAI_API_KEY="your-openai-key-here"
```

### Step 2: Start the Python Backend Server
Keep your terminal open inside the `backend` folder:

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the backend server
uvicorn main:app --reload --port 8000
```

### Step 3: Start the React Frontend Website
Open a **new terminal window**, navigate to the `frontend` directory:

```bash
# 1. Install Node modules
npm install

# 2. Start the website
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 📖 How to Use the Application

### 1. Ingesting Customer Data
Run the ingestion pipeline script to process the raw customer dataset into MongoDB:
```bash
python -c "from ingestion.customer_data_pipeline import pipeline; pipeline.ingest_dataset('path/to/your/dataset')"
```

### 2. Exploring the Customer Delight Dashboard
- Log in (default admin credentials exist for testing).
- View the tabular list of customers and their Risk Scores.
- Click **Analyze** on a high-risk customer to view their AI-generated Journey Timeline and Root Cause Analysis.

### 3. Escalation & Risk Management
- For high-risk customers, click **Request Escalation Manager**.
- An admin can use the Admin Dashboard to create a new user with the `risk-manager` role.
- Log in as the Risk Manager to view the dedicated Escalation Queue.
- Fill out the mandatory Actionable Work Items and Customer Feedback, then click **Resolve**.
- Watch as the background AI process incrementally updates the customer's timeline and lowers their risk score!

---

## 🗺️ Deep Dive Walkthrough
Want to learn more about how the incremental LLM updates and sentiment trajectory algorithms work? 
👉 **[Read the Full Technical Walkthrough Here](./Walkthrough.md)**
