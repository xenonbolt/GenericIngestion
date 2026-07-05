import time
from agents.utils import get_metrics
from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class RelevanceEvaluatorNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('relevance_evaluator', 'Running evaluator...')
        query = state["messages"][-1].content
        context = state.get("context", "")
        
        if not context or context == "No relevant context found.":
            await streamer.emit_node_completed('relevance_evaluator', get_metrics(start_time))
            return {"is_relevant": False}
            
        prompt = f"Evaluate if this context is relevant to the query. Query: '{query}'. Context: '{context[:500]}...'. Answer only 'yes' or 'no'."
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        is_relevant = "yes" in resp.content.lower()
        
        await streamer.emit_node_completed('relevance_evaluator', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
        return {"is_relevant": is_relevant}
