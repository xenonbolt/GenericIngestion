from langchain.chains import KuzuQAChain
from langchain_community.graphs import KuzuGraph
from agents.state import AgentState, streamer
from graph.kuzu_store import kuzu_store

class KuzuQANode:
    def __init__(self, llm):
        self.llm = llm
        try:
            self.kuzu_graph = KuzuGraph(kuzu_store.db)
            self.chain = KuzuQAChain.from_llm(llm=self.llm, graph=self.kuzu_graph, verbose=True)
        except Exception as e:
            print(f"Failed to init Kuzu QA Chain: {e}")
            self.chain = None

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('kuzu_qa', 'Running kuzu_qa...')
        query = state.get("translated_query", state["messages"][-1].content)
                
        try:
            if not self.chain:
                raise Exception("Chain not initialized")
            
            # KuzuGraph wraps it, but the chain generates Cypher from the schema
            self.kuzu_graph.refresh_schema()
            res = await self.chain.ainvoke({"query": query})
            output = res.get("result", str(res))
            
                        
            await streamer.emit_node_completed('kuzu_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            
            return {"kuzu_answer": output}
        except Exception as e:
            error_msg = f"Kuzu error: {str(e)}"
            await streamer.emit_node_completed('kuzu_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            return {"kuzu_answer": error_msg}
