import time
import json
import os
import re
from agents.utils import get_metrics
from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class GraphLibrarianNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('graph_librarian', 'Consulting Library TOC...')
        
        query = state.get("translated_query", state["messages"][-1].content)
        
        # Load master metadata (Table of Contents)
        master_metadata_path = os.path.join(os.getcwd(), "data", "master_chunk_metadata.json")
        toc_summary = ""
        
        if os.path.exists(master_metadata_path):
            try:
                with open(master_metadata_path, "r") as f:
                    master_metadata = json.load(f)
                    
                # Summarize TOC to fit in context window (e.g. top 100 entries or aggregated by file)
                entries = []
                for k, v in list(master_metadata.items())[:100]:
                    dtype = v.get("type", "unstructured")
                    fname = v.get("file_name", "Unknown File")
                    summary = v.get("summary", "")
                    kw = ", ".join(v.get("keywords", []))
                    entries.append(f"- ID: {k} | Type: {dtype} | File: {fname} | Keywords: {kw} | Summary: {summary}")
                
                toc_summary = "\n".join(entries)
            except Exception as e:
                print(f"Error loading master metadata: {e}")
                
        if not toc_summary:
            toc_summary = "No library files indexed yet."

        prompt = f"""You are the Graph Librarian. The user is asking a question. Here is the library's Table of Contents (metadata for all available files and chunks):
{toc_summary}

Based on the user's query: '{query}'
Determine the best strategy to answer this query.
Do we need to perform structured tabular data analysis using the Pandas Agent? Do we need to perform semantic Vector Search for unstructured text? Or both?

Return a JSON object strictly following this format:
{{
  "use_vector_search": true or false,
  "use_pandas_agent": true or false,
  "vector_search_queries": ["specific semantic search queries for vector DB"],
  "pandas_tasks": ["specific tabular tasks for the data agent"]
}}

Only output the raw JSON.
"""

        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        use_vector = True
        use_pandas = False
        vector_queries = [query]
        pandas_tasks = []
        
        try:
            match = re.search(r'\{.*\}', resp.content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                use_vector = data.get("use_vector_search", True)
                use_pandas = data.get("use_pandas_agent", False)
                vector_queries = data.get("vector_search_queries", [query])
                pandas_tasks = data.get("pandas_tasks", [])
                
                if not use_vector and not use_pandas:
                    use_vector = True # Fallback
        except Exception as e:
            print("Librarian parsing error:", e)
            
        await streamer.emit_node_completed('graph_librarian', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
        
        return {
            "use_vector": use_vector,
            "use_pandas": use_pandas,
            "tasks": vector_queries, # For the retrieval synthesizer
            "pandas_tasks": pandas_tasks # For the data analysis node
        }
