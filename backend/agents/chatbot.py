import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from telemetry import setup_telemetry
setup_telemetry()

from memory.mongo_memory import MongoMemoryManager
from memory.vector_memory import VectorMemoryManager
from memory.token_manager import TokenManager

from agents.state import AgentState

from agents.nodes.ticket_analysis_node import ticket_analysis_node
from agents.nodes.transcript_analysis_node import transcript_analysis_node
from agents.nodes.overall_decision_node import overall_decision_node

class ChatbotAgent:
    def __init__(self, memory_manager: MongoMemoryManager, token_manager: TokenManager):
        self.memory_manager = memory_manager
        self.vector_memory_manager = VectorMemoryManager()
        self.token_manager = token_manager
        from monitoring.observability import obs_manager
        callbacks = [obs_manager.langfuse_handler] if obs_manager.langfuse_handler else []
        
        llm_provider = os.getenv("LLM_PROVIDER", "google").lower()
        if llm_provider == "openai":
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
            
            # Setup kwargs for ChatOpenAI, including Headroom proxy if configured
            llm_kwargs = {
                "model": model_name,
                "temperature": 0.2,
                "callbacks": callbacks
            }
            
            # Route requests through Headroom proxy if configured
            headroom_proxy = os.getenv("HEADROOM_PROXY")
            if headroom_proxy:
                llm_kwargs["base_url"] = headroom_proxy
                
            self.llm = ChatOpenAI(**llm_kwargs)
            self.token_manager.model_name = model_name
        else:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2, callbacks=callbacks)
            
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add Nodes
        workflow.add_node("ticket_analysis_node", ticket_analysis_node)
        workflow.add_node("transcript_analysis_node", transcript_analysis_node)
        workflow.add_node("overall_decision_node", overall_decision_node)
        
        # Define Edges
        workflow.add_edge(START, "ticket_analysis_node")
        workflow.add_edge("ticket_analysis_node", "transcript_analysis_node")
        workflow.add_edge("transcript_analysis_node", "overall_decision_node")
        workflow.add_edge("overall_decision_node", END)
        
        return workflow.compile()

    async def invoke(self, session_id: str, user_id: str, human_input: str):
        history = self.memory_manager.get_messages(session_id)
        messages = [HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"]) for m in history]
        messages.append(HumanMessage(content=human_input))
        
        target_customer_id = ""
        if human_input.startswith("ANALYZE_CUSTOMER:"):
            target_customer_id = human_input.split("ANALYZE_CUSTOMER:")[1].strip()

        state = {
            "session_id": session_id, 
            "user_id": user_id, 
            "messages": messages, 
            "translated_query": "",
            "intent": "", 
            "target_customer_id": target_customer_id,
            "tasks": [],
            "pandas_tasks": [],
            "use_vector": False,
            "use_pandas": False,
            "context": "", 
            "pandas_context": "",
            "networkx_answer": "",
            "kuzu_answer": "",
            "is_relevant": False
        }
        from monitoring.observability import obs_manager
        config = {}
        if obs_manager.langfuse_handler:
            config["callbacks"] = [obs_manager.langfuse_handler]
        
        result = await self.graph.ainvoke(state, config=config)
        return result["messages"][-1].content
