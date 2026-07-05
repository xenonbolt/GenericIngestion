import time
from agents.utils import get_metrics
from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class IntentAnalyzerNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('intent_analyzer', 'Running intent...')
        query_to_analyze = state.get("translated_query", state["messages"][-1].content)
        prompt = f"""Analyze the following user query: '{query_to_analyze}'.
Which of the following internal capabilities is best suited to answer it?
1) 'data_analysis': If the query requires quantitative counting, filtering, aggregating, or tabular data analysis (e.g., questions like "how many people", "what is the average", or filtering by demographics like city).
2) 'graph_search': Use ONLY if the query explicitly mentions graphs, networks, shortest paths, or highly complex structural network analysis.
3) 'search': Use this for ALL general factual questions, information retrieval, or questions about unstructured text, PDFs, and general entities (e.g., "who is the client for X", "what is Y"). This is the default for most knowledge lookup.
4) 'chat': General conversation.

Output ONLY the category name (e.g. 'data_analysis', 'graph_search', 'search', or 'chat')."""
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        response_text = resp.content.lower().strip()
        if "data_analysis" in response_text:
            intent = "data_analysis"
        elif "graph_search" in response_text:
            intent = "graph_search"
        elif "search" in response_text:
            intent = "search"
        else:
            intent = "chat"
        
        await streamer.emit_node_completed('intent_analyzer', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
        return {"intent": intent}
