from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class RelevanceEvaluatorNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('relevance_evaluator', 'Running evaluator...')
        query = state["messages"][-1].content
        context = state.get("context", "")
        
        if not context or context == "No relevant context found.":
            await streamer.emit_node_completed('relevance_evaluator', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            return {"is_relevant": False}
            
        prompt = f"Evaluate if this context is relevant to the query. Query: '{query}'. Context: '{context[:500]}...'. Answer only 'yes' or 'no'."
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        is_relevant = "yes" in resp.content.lower()
        
        await streamer.emit_node_completed('relevance_evaluator', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
        return {"is_relevant": is_relevant}
