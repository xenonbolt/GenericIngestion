import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END

from memory.mongo_memory import MongoMemoryManager
from memory.token_manager import TokenManager

from agents.state import AgentState
from agents.nodes.translator_node import QueryTranslatorNode
from agents.nodes.intent_node import IntentAnalyzerNode
from agents.nodes.decomposer_node import TaskDecomposerNode
from agents.nodes.retrieval_node import RetrievalSynthesizerNode
from agents.nodes.evaluator_node import RelevanceEvaluatorNode
from agents.nodes.generator_node import GeneratorNode
from agents.nodes.data_analysis_node import DataAnalysisNode
from agents.nodes.networkx_qa_node import NetworkXQANode
from agents.nodes.kuzu_qa_node import KuzuQANode
from agents.nodes.graph_judge_node import GraphJudgeNode

class ChatbotAgent:
    def __init__(self, memory_manager: MongoMemoryManager, token_manager: TokenManager):
        self.memory_manager = memory_manager
        self.token_manager = token_manager
        from monitoring.observability import obs_manager
        callbacks = [obs_manager.langfuse_handler] if obs_manager.langfuse_handler else []
        
        llm_provider = os.getenv("LLM_PROVIDER", "google").lower()
        if llm_provider == "openai":
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
            self.llm = ChatOpenAI(model=model_name, temperature=0.2, callbacks=callbacks)
            self.token_manager.model_name = model_name
        else:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2, callbacks=callbacks)
            
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # Instantiate Node Classes
        translator = QueryTranslatorNode(self.llm)
        intent = IntentAnalyzerNode(self.llm)
        decomposer = TaskDecomposerNode(self.llm)
        retrieval = RetrievalSynthesizerNode(self.llm)
        evaluator = RelevanceEvaluatorNode(self.llm)
        data_analysis = DataAnalysisNode(self.llm)
        nx_qa = NetworkXQANode(self.llm)
        kuzu_qa = KuzuQANode(self.llm)
        graph_judge = GraphJudgeNode(self.llm)
        generator = GeneratorNode(self.llm, self.memory_manager, self.token_manager)
        
        # Add Nodes
        workflow.add_node("query_translator", translator)
        workflow.add_node("intent_analyzer", intent)
        workflow.add_node("task_decomposer", decomposer)
        workflow.add_node("retrieval_synthesizer", retrieval)
        workflow.add_node("relevance_evaluator", evaluator)
        workflow.add_node("data_analysis", data_analysis)
        workflow.add_node("networkx_qa", nx_qa)
        workflow.add_node("kuzu_qa", kuzu_qa)
        workflow.add_node("graph_judge", graph_judge)
        workflow.add_node("generator_agent", generator)
        
        # Define Edges
        workflow.add_edge(START, "query_translator")
        workflow.add_edge("query_translator", "intent_analyzer")
        
        workflow.add_conditional_edges(
            "intent_analyzer",
            lambda state: state.get("intent", "chat"),
            {
                "search": "task_decomposer",
                "data_analysis": "data_analysis",
                "graph_search": "networkx_qa",
                "chat": "generator_agent"
            }
        )
        
        workflow.add_edge("data_analysis", "generator_agent")
        
        # Sequential dual graph retrieval
        workflow.add_edge("networkx_qa", "kuzu_qa")
        workflow.add_edge("kuzu_qa", "graph_judge")
        workflow.add_edge("graph_judge", "generator_agent")
        
        workflow.add_edge("task_decomposer", "retrieval_synthesizer")
        workflow.add_edge("retrieval_synthesizer", "relevance_evaluator")
        
        # Conditional routing from relevance
        workflow.add_conditional_edges(
            "relevance_evaluator",
            lambda state: "generate" if state.get("is_relevant") else "generate", # fallback to generate anyway but with poor context flag
            {
                "generate": "generator_agent"
            }
        )
        
        workflow.add_edge("generator_agent", END)
        return workflow.compile()

    async def invoke(self, session_id: str, user_id: str, human_input: str):
        history = self.memory_manager.get_messages(session_id)
        messages = [HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"]) for m in history]
        messages.append(HumanMessage(content=human_input))
        
        state = {
            "session_id": session_id, 
            "user_id": user_id, 
            "messages": messages, 
            "translated_query": "",
            "intent": "", 
            "tasks": [],
            "context": "", 
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
