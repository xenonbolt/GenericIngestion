# Enterprise Customer Intelligence Platform Walkthrough

Welcome to the comprehensive walkthrough of the Universal Customer Intelligence Platform! This document details the advanced capabilities and architectural decisions implemented across the stack to manage customer risk, timelines, and escalations.

## 1. Automated Customer Intelligence (LLM Ingestion)
The core intelligence of the platform relies on automated, batch-processed analysis of raw customer interaction data (e.g., ServiceNow incidents or Zendesk tickets).
- **Data Ingestion Pipeline:** The `CustomerDataPipeline` processes raw JSON ticket dumps.
- **Holistic Timeline Generation:** Instead of analyzing tickets in isolation, the AI aggregates all events occurring on the same day into a unified `Customer Journey Timeline`.
- **Sentiment Trajectory:** The LLM evaluates sentiment dynamically. Instead of a simple mathematical average, it evaluates the *trajectory* of the day (e.g., starting frustrated but ending satisfied leads to a "Positive Resolution" sentiment).
- **Risk Profiling:** The system automatically calculates an `Escalation Risk Score (0-100)` based on SLA breaches, repeated issues, and negative sentiment.

## 2. Customer Delight Dashboard
The primary interface for CX (Customer Experience) analysts.
- **Tabular Risk Matrix:** Displays all customers, their account tiers, and their real-time escalation risk scores.
- **Detailed Analysis Panel:** Clicking on a customer reveals their complete Journey Timeline, root cause analysis of their current issues, and AI-recommended Next Best Actions.
- **Risk Threshold Triggers:** If a customer's Escalation Risk exceeds 50%, the platform automatically surfaces a "Request Escalation Manager" workflow.

## 3. Risk Manager Escalation Workflow
A dedicated workflow for handling high-risk accounts.
- **Role-Based Access Control:** Administrators can create users and assign them the `risk-manager` role using the Enterprise Admin Operations Control panel.
- **Escalation Queue:** Risk Managers have access to a dedicated dashboard displaying all open escalation tickets.
- **Actionable Work Items:** Managers must review the AI's "Next Best Actions" and document the specific work they performed against each action.
- **Customer Feedback Loop:** Managers capture and log direct customer feedback upon resolving the issue.

## 4. Incremental AI Re-Analysis
To ensure the system remains performant and cost-effective, resolving an escalation does *not* trigger a full re-processing of a customer's historical data.
- **Delta Updates:** When an escalation ticket is marked "Resolved", the backend triggers an asynchronous background task (`incremental_update_customer`).
- **Knowledge Base Prompting:** The LLM is provided the customer's *existing* profile (timeline, sentiment, risk score) as a knowledge base.
- **Intelligent Recalculation:** The LLM evaluates the manager's actionable work items and the new customer feedback to output an incrementally updated timeline and a newly adjusted (typically lowered) Risk Score.

---
*Run `npm run dev` in the frontend and `uvicorn main:app` in the backend to start exploring these features!*
