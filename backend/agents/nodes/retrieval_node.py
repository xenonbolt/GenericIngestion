import time
from agents.utils import get_metrics
from agents.state import AgentState, streamer
from ingestion.pipeline import pipeline
from graph.networkx_store import kg_store
from langchain_core.messages import HumanMessage
import json

class RetrievalSynthesizerNode:
    def __init__(self, llm, mongo_memory):
        self.llm = llm
        self.mongo_memory = mongo_memory

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('retrieval_synthesizer', 'Running semantic search...')
                
        tasks = state.get("tasks", [state.get("translated_query", state["messages"][-1].content)])
        combined_context = []
        attempts = state.get("retrieval_attempts") or 0
        
        for idx, task in enumerate(tasks):
            # 1. Pre-Retrieval Document Selection
            raw_docs = self.mongo_memory.get_all_raw_documents()
            if not raw_docs:
                combined_context.append("No documents available in knowledge base.")
                continue
                
            doc_summaries = "\n".join([
                f"ID: {d['doc_id']} | File: {d.get('file_name')} | Keywords: {d.get('keywords')} | Summary: {d.get('summary')}"
                for d in raw_docs
            ])
            
            prompt = f"""You are a document routing agent. Review the user's query and the available documents.
User Query: {task}

Available Documents:
{doc_summaries}

Which document is most likely to contain the answer? Output ONLY a JSON object with the doc_id. If NO document seems relevant, output "NONE" for the doc_id.
Format: {{"doc_id": "1234-uuid"}} or {{"doc_id": "NONE"}}"""
            
            try:
                resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
                resp_text = resp.content.strip()
                if resp_text.startswith("```json"): resp_text = resp_text[7:]
                if resp_text.startswith("```"): resp_text = resp_text[3:]
                if resp_text.endswith("```"): resp_text = resp_text[:-3]
                parsed = json.loads(resp_text)
                selected_doc_id = parsed.get("doc_id", "NONE")
            except Exception as e:
                print("Failed to route document:", e)
                selected_doc_id = "NONE"
                
            if selected_doc_id == "NONE":
                combined_context.append(f"--- Context for task: {task} ---\nNo relevant documents found. Ask the user for more details.")
                continue
                
            # 2. Lazy Embedding (Just-In-Time)
            full_doc = self.mongo_memory.get_raw_document(selected_doc_id)
            if not full_doc:
                continue
                
            file_name = full_doc.get("file_name", "Unknown")
            if not full_doc.get("is_embedded", False):
                print(f"Lazy Embedding Triggered for {file_name}...")
                await streamer.emit_node_active('retrieval_synthesizer', f'Lazy embedding {file_name}...')
                text = full_doc.get("text", "")
                if text.strip():
                    chunks = pipeline.text_splitter.split_text(text)
                    ids = [f"{selected_doc_id}_chunk_{i}" for i in range(len(chunks))]
                    metadatas = [{"file_name": file_name, "doc_id": selected_doc_id, "chunk_index": i} for i in range(len(chunks))]
                    
                    pipeline.collection.add(
                        documents=chunks,
                        metadatas=metadatas,
                        ids=ids
                    )
                    self.mongo_memory.set_document_embedded(selected_doc_id)
            
            # 3. Vector Search (Scoped to the selected document)
            offset = attempts * 15
            try:
                results = pipeline.collection.query(
                    query_texts=[task], 
                    n_results=15 + offset,
                    where={"doc_id": selected_doc_id}
                )
                docs = results.get("documents", [[]])[0]
                vector_texts = docs[offset:] if docs else []
            except Exception as e:
                print("Vector search error:", e)
                vector_texts = []
            
            combined_context.append(f"--- Context for task: {task} ---")
            if vector_texts: 
                combined_context.append(f"Semantic Documents (from {file_name}):\n" + "\n".join(vector_texts))
            else:
                combined_context.append("No relevant chunks found within the selected document.")
            
        final_context = "\n".join(combined_context) if combined_context else "No relevant context found."
        
        await streamer.emit_node_completed('retrieval_synthesizer', get_metrics(start_time))
        
        return {"context": final_context, "retrieval_attempts": attempts + 1}
