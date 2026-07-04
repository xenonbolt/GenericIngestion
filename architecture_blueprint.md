# Universal Agentic Intelligence Platform Architecture

## Overview
This platform is a generic, usecase-agnostic Multi-Agent Architecture built on **LangGraph**. It acts as an enterprise-grade foundation that can be specialized for different business domains by simply updating the agent definitions and tools. The system ensures robust data ingestion, dual-layer conversational memory, global security compliance for proxy-restricted environments, and rich real-time observability.

## 1. Architectural & Multimodal Data Ingestion
- **Generic LangGraph Engine:** The core workflow engine is built using LangGraph, offering fine-grained control over agent states and transitions.
- **Multimodal Pipeline:** Documents (PDFs, text) and images are parsed through a unified ingestion layer.
- **Structured Data Handling:** Raw CSV data is handled explicitly without being injected directly into a standard Vector DB. Instead, tabular data is parsed, chunked, and represented as nodes and edges in a local Graph database for precise relationship querying.

## 2. Graph & Knowledge Management
- **NetworkX Integration:** Due to local constraints (e.g., restricted lab environments where Neo4j may be unavailable), the platform utilizes **NetworkX** as its primary in-memory Graph database framework.
- It maps structured data (like CSVs) and entity relationships to semantic structures that agents can query.

## 3. Memory, State, & Token Optimization
- **Dual-Layer Memory (MongoDB):**
  - *Short-term Memory:* Context windows for ongoing conversations.
  - *Long-term Memory:* Persistent extraction of user preferences, history, and domain-specific knowledge across sessions.
- **Headroom & Token Optimization:** Utilizing `tiktoken`, the system explicitly tracks context window sizes. Before an LLM call is made, it computes the remaining "headroom". If the window is near its limit, short-term history is dynamically truncated or summarized to prevent overflow and save cost.

## 4. Governance, Observability, and UI
- **Agent Traceability:** Every tool call and state transition within LangGraph is logged and broadcasted.
- **Observability Stack:** Hooks for PostHog (analytics), Langfuse (tracing), and Ragas (evaluation) are integrated directly into the event stream.
- **Live Trace UI:** A React-based frontend using `React Flow` subscribes to a WebSocket endpoint (`/ws/agent-stream`). It visually renders the LangGraph tool-calling tree and state transitions in real time, enabling developers and users to watch the agent "think" dynamically.

## 5. Security & Network Compliance
- **Global SSL Bypass:** Designed for strict corporate labs with deep packet inspection and custom proxies. A global middleware utility disables SSL verification for outgoing requests across standard libraries (`requests`, `httpx`, `urllib3`, and standard `ssl` contexts). *Warning: For lab use only.*
