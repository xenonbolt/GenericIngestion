from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class GraphJudgeNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('graph_judge', 'Running graph_judge...')
        query = state.get("translated_query", state["messages"][-1].content)
        nx_ans = state.get("networkx_answer", "")
        kz_ans = state.get("kuzu_answer", "")
        
                
        prompt = f"""
You are an intelligent judge evaluating two different graph database traversals.
The user asked: "{query}"

Output from NetworkX (Programmatic Python Graph):
{nx_ans}

Output from KùzuDB (Cypher Query Graph):
{kz_ans}

Evaluate which of these outputs provides a more accurate, complete, or structurally sound answer to the query.
If one failed with an error, choose the other. If both are good, pick the one with better detail.
Respond only with the text of the chosen answer, optionally appending a short note on why it was chosen. Do not include your internal reasoning process in the final output text.
"""
        try:
            resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
            best_context = f"--- Selected Graph Context ---\n{resp.content}"
            
                        
            await streamer.emit_node_completed('graph_judge', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            
            return {"context": best_context, "is_relevant": True}
        except Exception as e:
            fallback = f"Judge failed. Nx: {nx_ans} | Kz: {kz_ans}"
            await streamer.emit_node_completed('graph_judge', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            return {"context": fallback}
