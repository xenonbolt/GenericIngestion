import time
import json
from agents.utils import get_metrics
from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class IntentAnalyzerNode:
    def __init__(self, llm, vector_memory_manager=None, mongo_memory_manager=None):
        self.llm = llm
        self.vector_memory = vector_memory_manager
        self.mongo_memory = mongo_memory_manager

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('intent_analyzer', 'Analyzing intent and extracting memory...')
        query_to_analyze = state.get("translated_query", state["messages"][-1].content)
        
        prompt = f"""Analyze the following user query: '{query_to_analyze}'.

1. Determine the intent:
- 'data_analysis': If the query asks to analyze datasets (counting, filtering, aggregating data). NOT for personal statements.
- 'graph_search': Explicitly mentions graphs, networks, shortest paths.
- 'search': General factual questions about unstructured text or knowledge base lookup.
- 'chat': General conversation, greetings, OR personal statements about the user themselves (e.g. "My name is...", "I live in...", "I like...").

2. Extract any memory actions the user implies about themselves. The user might state new facts (ADD), update existing facts (UPDATE), or ask you to forget something (DELETE).
- "I moved to NY" -> ADD "User moved to NY" or UPDATE if they previously stated a location.
- "Forget my favorite color" -> DELETE "User's favorite color is ..."

Output ONLY valid JSON in this exact format:
{{
    "intent": "chat",
    "memory_actions": [
        {{"action": "ADD", "memory": "User's name is Almighty"}},
        {{"action": "UPDATE", "old_memory": "User lives in Kolkata", "new_memory": "User lives in Bangalore"}},
        {{"action": "DELETE", "memory": "User's favorite color is blue"}}
    ]
}}
If no memory operations are needed, return an empty array for memory_actions.
"""
        
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        response_text = resp.content.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        try:
            parsed = json.loads(response_text)
            intent = parsed.get("intent", "chat").lower()
            actions = parsed.get("memory_actions", [])
            
            # Execute Memory Actions using VectorMemoryManager
            if self.vector_memory and actions and isinstance(actions, list):
                user_id = state.get("user_id")
                for act in actions:
                    action_type = act.get("action")
                    if action_type == "ADD" and act.get("memory"):
                        self.vector_memory.add_memory(user_id, act["memory"])
                    elif action_type == "DELETE" and act.get("memory"):
                        self.vector_memory.delete_memory(user_id, act["memory"])
                    elif action_type == "UPDATE" and act.get("old_memory") and act.get("new_memory"):
                        self.vector_memory.update_memory(user_id, act["old_memory"], act["new_memory"])
                    
        except json.JSONDecodeError:
            print(f"[Intent Error] Failed to parse JSON: {response_text}")
            if "data_analysis" in response_text.lower():
                intent = "data_analysis"
            elif "graph_search" in response_text.lower():
                intent = "graph_search"
            elif "search" in response_text.lower():
                intent = "search"
            else:
                intent = "chat"
                
        valid_intents = ["data_analysis", "graph_search", "search", "chat"]
        if intent not in valid_intents:
            intent = "chat"
        
        await streamer.emit_node_completed('intent_analyzer', get_metrics(start_time, locals().get('resp')))
        return {"intent": intent}
