import re
import json
from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class TaskDecomposerNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('task_decomposer', 'Running decomposer...')
        translated = state.get("translated_query", "")
        prompt = (
            "You are a task decomposer. Break down the following search query into a JSON list of 1 to 3 distinct, specific search tasks.\n"
            f"Query: '{translated}'\n"
            "Format your output strictly as a JSON array of strings. Example: [\"Find statistics on X\", \"Retrieve summary of Y\"]"
        )
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        tasks = [translated] # fallback
        try:
            match = re.search(r'\[.*\]', resp.content, re.DOTALL)
            if match:
                tasks = json.loads(match.group(0))
        except Exception:
            pass
            
        await streamer.emit_node_completed('task_decomposer', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
        return {"tasks": tasks}
