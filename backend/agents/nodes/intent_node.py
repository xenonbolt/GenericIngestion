from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class IntentAnalyzerNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('intent_analyzer', 'Running intent...')
        query_to_analyze = state.get("translated_query", state["messages"][-1].content)
        prompt = f"""Analyze the following user query: '{query_to_analyze}'.
Which of the following internal capabilities is best suited to answer it?
1) 'data_analysis': If the query requires quantitative counting, filtering, aggregating, or tabular data analysis (e.g., questions like "how many people", "what is the average", or filtering by demographics like city).
2) 'graph_search': If it requires finding relationships, paths, connections, or structural links between entities in a network/graph.
3) 'search': If it requires looking up semantic text in external files, pdfs, or general unstructured data.
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
        
        await streamer.emit_node_completed('intent_analyzer', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
        return {"intent": intent}
