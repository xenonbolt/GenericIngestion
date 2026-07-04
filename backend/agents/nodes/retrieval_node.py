from agents.state import AgentState, streamer
from ingestion.pipeline import pipeline
from graph.networkx_store import kg_store

class RetrievalSynthesizerNode:
    def __init__(self, llm):
        self.llm = llm # Note: LLM not strictly needed here unless we do reranking, but good for consistency

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('retrieval_synthesizer', 'Running retrieval...')
                
        tasks = state.get("tasks", [state.get("translated_query", state["messages"][-1].content)])
        combined_context = []
        
        for idx, task in enumerate(tasks):
                        
            # Vector Search (Semantic)
            attempts = state.get("retrieval_attempts") or 0
            offset = attempts * 15
            try:
                results = pipeline.collection.query(query_texts=[task], n_results=15 + offset)
                docs = results.get("documents", [[]])[0]
                # Slice to get only the new chunk batch if looping
                vector_texts = docs[offset:] if docs else []
            except Exception as e:
                print("Vector search error:", e)
                vector_texts = []
            
            # Graph Search (Structured)
            graph_context = ""
            try:
                words = task.split()
                for word in words:
                    rels = kg_store.query_relationships(word)
                    for r in rels:
                        graph_context += f"- {r['source']} is linked to {r['target']} via {r['relation']}\n"
            except Exception as e:
                print("Graph search error:", e)
            
            combined_context.append(f"--- Context for task: {task} ---")
            if vector_texts: 
                combined_context.append("Semantic Documents:\n" + "\n".join(vector_texts))
            if graph_context: 
                combined_context.append("Knowledge Graph Relations:\n" + graph_context)
            
        final_context = "\n".join(combined_context) if len(combined_context) > len(tasks) else "No relevant context found."
        
        await streamer.emit_node_completed('retrieval_synthesizer', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
        
        return {"context": final_context, "retrieval_attempts": attempts + 1}
