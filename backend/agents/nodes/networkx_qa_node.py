from langchain.chains import GraphQAChain
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from agents.state import AgentState, streamer
from graph.networkx_store import kg_store

class NetworkXQANode:
    def __init__(self, llm):
        self.llm = llm
        # Load the graph from the global store
        self.nx_graph = NetworkxEntityGraph(kg_store.graph)
        try:
            self.chain = GraphQAChain.from_llm(llm=self.llm, graph=self.nx_graph, verbose=True)
        except Exception as e:
            print(f"Failed to init NetworkX QA Chain: {e}")
            self.chain = None

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('networkx_qa', 'Running networkx_qa...')
        query = state.get("translated_query", state["messages"][-1].content)
                
        try:
            if not self.chain:
                raise Exception("Chain not initialized")
            # ainvoke yields to the asyncio event loop
            res = await self.chain.ainvoke({"query": query})
            output = res.get("result", str(res))
            
                        
            await streamer.emit_node_completed('networkx_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            
            return {"networkx_answer": output}
        except Exception as e:
            error_msg = f"NetworkX error: {str(e)}"
            await streamer.emit_node_completed('networkx_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            return {"networkx_answer": error_msg}
