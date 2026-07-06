import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from openinference.instrumentation.langchain import LangChainInstrumentor

# Initialize standard OpenTelemetry to send traces to Phoenix
resource = Resource(attributes={"project.name": os.getenv("PHOENIX_PROJECT_NAME", "default")})
tracer_provider = TracerProvider(resource=resource)
endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006") + "/v1/traces"
tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
trace.set_tracer_provider(tracer_provider)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

from memory.mongo_memory import MongoMemoryManager
from memory.vector_memory import VectorMemoryManager
from memory.token_manager import TokenManager

from agents.state import AgentState
from agents.nodes.translator_node import QueryTranslatorNode
from agents.nodes.intent_node import IntentAnalyzerNode
from agents.nodes.retrieval_node import RetrievalSynthesizerNode
from agents.nodes.evaluator_node import RelevanceEvaluatorNode
from agents.nodes.generator_node import GeneratorNode
from agents.nodes.data_analysis_node import DataAnalysisNode
from agents.nodes.librarian_node import GraphLibrarianNode

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
        
        # Instantiate Node Classes
        translator = QueryTranslatorNode(self.llm)
        intent = IntentAnalyzerNode(self.llm, self.vector_memory_manager, self.memory_manager)
        librarian = GraphLibrarianNode(self.llm)
        retrieval = RetrievalSynthesizerNode(self.llm)
        evaluator = RelevanceEvaluatorNode(self.llm)
        data_analysis = DataAnalysisNode(self.llm)
        generator = GeneratorNode(self.llm, self.memory_manager, self.token_manager, self.vector_memory_manager)
        
        # Add Nodes
        workflow.add_node("query_translator", translator)
        workflow.add_node("intent_analyzer", intent)
        workflow.add_node("graph_librarian", librarian)
        workflow.add_node("retrieval_synthesizer", retrieval)
        workflow.add_node("relevance_evaluator", evaluator)
        workflow.add_node("data_analysis", data_analysis)
        workflow.add_node("generator_agent", generator)
        
        # Define Edges
        workflow.add_edge(START, "query_translator")
        workflow.add_edge("query_translator", "intent_analyzer")
        
        workflow.add_conditional_edges(
            "intent_analyzer",
            lambda state: state.get("intent", "chat"),
            {
                "search": "graph_librarian",
                "data_analysis": "graph_librarian",
                "graph_search": "graph_librarian",
                "chat": "generator_agent"
            }
        )
        
        # Sequential context gathering pipeline defined by the Librarian
        def route_from_librarian(state):
            if state.get("use_pandas"): return "data_analysis"
            if state.get("use_vector"): return "retrieval_synthesizer"
            return "relevance_evaluator"
            
        workflow.add_conditional_edges(
            "graph_librarian",
            route_from_librarian,
            {
                "data_analysis": "data_analysis",
                "retrieval_synthesizer": "retrieval_synthesizer",
                "relevance_evaluator": "relevance_evaluator"
            }
        )
        
        def route_from_data_analysis(state):
            if state.get("use_vector"): return "retrieval_synthesizer"
            return "relevance_evaluator"
            
        workflow.add_conditional_edges(
            "data_analysis",
            route_from_data_analysis,
            {
                "retrieval_synthesizer": "retrieval_synthesizer",
                "relevance_evaluator": "relevance_evaluator"
            }
        )
        
        workflow.add_edge("retrieval_synthesizer", "relevance_evaluator")
        
        # Conditional routing from relevance
        def route_relevance(state):
            if state.get("is_relevant"):
                return "generate"
            elif state.get("retrieval_attempts", 0) < 3:
                return "retry_retrieval"
            else:
                return "generate"

        workflow.add_conditional_edges(
            "relevance_evaluator",
            route_relevance,
            {
                "generate": "generator_agent",
                "retry_retrieval": "retrieval_synthesizer"
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
