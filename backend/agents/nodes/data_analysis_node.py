import time
from agents.utils import get_metrics
import os
import pandas as pd
from langchain_experimental.agents import create_pandas_dataframe_agent
from agents.state import AgentState, streamer

class DataAnalysisNode:
    def __init__(self, llm):
        self.llm = llm
        self.uploads_dir = os.path.join(os.getcwd(), "data", "uploads")

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('data_analysis', 'Running data_analysis...')
        tasks = state.get("pandas_tasks", [])
        if tasks:
            query = " ".join(tasks)
        else:
            query = state.get("translated_query", state["messages"][-1].content)
                
        # Discover all CSVs
        if not os.path.exists(self.uploads_dir):
            await streamer.emit_node_completed('data_analysis', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
            return {"pandas_context": "No tabular datasets found on the server."}
            
        csv_files = [f for f in os.listdir(self.uploads_dir) if f.endswith(".csv")]
        if not csv_files:
            await streamer.emit_node_completed('data_analysis', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
            return {"pandas_context": "No tabular datasets found on the server."}
            
        # Load CSVs into DataFrames
        dataframes = []
        df_names = []
        for file in csv_files:
            try:
                df = pd.read_csv(os.path.join(self.uploads_dir, file))
                dataframes.append(df)
                df_names.append(file)
            except Exception as e:
                print(f"Failed to load {file}: {e}")
                
        if not dataframes:
            await streamer.emit_node_completed('data_analysis', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
            return {"pandas_context": "Failed to load any valid tabular datasets."}
            
                
        # Initialize the LangChain Pandas Agent
        try:
            # allow_dangerous_code=True is required by langchain_experimental for python execution
            agent = create_pandas_dataframe_agent(
                self.llm, 
                dataframes, 
                verbose=True, 
                agent_type="zero-shot-react-description",
                allow_dangerous_code=True,
                handle_parsing_errors=True
            )
            
            # Execute the query
            response = await agent.ainvoke({"input": f"You are analyzing the following datasets: {df_names}. Query: {query}"})
            output = response.get("output", str(response))
            
                        
            # Format context so the final generator uses it
            final_context = f"--- Pandas Data Analysis Result ---\n{output}"
            await streamer.emit_node_completed('data_analysis', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
            return {"pandas_context": final_context, "is_relevant": True}
            
        except Exception as e:
            print(f"Pandas agent error: {e}")
            await streamer.emit_node_completed('data_analysis', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
            return {"pandas_context": f"Failed to perform tabular data analysis. Error: {str(e)}"}
