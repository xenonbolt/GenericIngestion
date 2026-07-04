# Enterprise AI Agent Platform Walkthrough

Welcome to the comprehensive walkthrough of the Universal Agentic Intelligence Platform! This document details the advanced capabilities and architectural decisions implemented across the stack.

## 1. Multi-Agent Orchestration (LangGraph)
The core intelligence of the platform is driven by a sophisticated Directed Acyclic Graph (DAG) using LangGraph. The `ChatbotAgent` orchestrates multiple specialized nodes:
- **Query Translator:** Translates ambiguous conversational queries into precise search intents based on chat history.
- **Intent Analyzer:** Classifies intents to route the graph (e.g., direct chat, vector search, graph search, data analysis).
- **Task Decomposer:** Breaks down complex external search requests into manageable sub-tasks.
- **Retrieval Synthesizer:** Executes vector similarity searches against ChromaDB.
- **Graph Agents (NetworkX & Kuzu):** Specialized agents that execute programmatic graph traversal and Cypher queries to extract relationships.
- **Pandas Data Agent:** A specialized Python REPL agent that dynamically writes and executes pandas code to analyze tabular CSV datasets on the fly.
- **Relevance Evaluator:** An LLM-as-a-Judge node that grades retrieved contexts to prevent hallucinations.
- **Generator Agent:** Synthesizes all gathered intelligence into the final response.

## 2. Advanced Real-Time Telemetry & Observability
The platform features enterprise-grade tracing and observability:
- **Langfuse Integration:** Global tracing is implemented at the lowest LLM layer. Every sub-agent, tool execution, and node transition is recorded and streamed to your Langfuse dashboard.
- **Live React Flow DAG:** The frontend visualizes the agent's brain in real-time. As the backend traverses the LangGraph nodes, it broadcasts WebSockets events (`node_active`, `node_completed`). The React Flow canvas instantly updates, displaying live latency, token usage, and execution paths.

## 3. Multimodal Data Ingestion
The system supports diverse unstructured and structured data:
- **Unstructured Data (PDF, Image, Text):** Processed via local embedding models into ChromaDB.
- **Structured Data (CSV):** Seamlessly ingested. The system can map structural entities into NetworkX/Kuzu graphs or analyze them dynamically using the Pandas agent.
- **Auto-Fill Metadata:** The frontend features an "Auto-Fill" magic wand that uses Gemini's Vision/Audio models to automatically extract a summary, category, and tags from uploaded files before ingestion.

## 4. Short-Term & Long-Term Memory
- **Short-Term Memory:** Uses `MongoMemoryManager` to preserve conversational context across the session, allowing for natural follow-up questions.
- **Long-Term Memory:** Historical data is persisted permanently in MongoDB, allowing agents to access past user preferences and contexts.

---
*Run `npm run dev` in the frontend and `uvicorn main:app` in the backend to start exploring these features!*
