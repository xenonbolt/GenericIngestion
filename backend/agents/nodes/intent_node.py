import time
import json
from agents.utils import get_metrics
from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class IntentAnalyzerNode:
    def __init__(self, llm, memory_manager=None):
        self.llm = llm
        self.memory_manager = memory_manager

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

2. Extract any personal facts the user shares about themselves as key-value pairs (e.g. name, location, preferences). If none, return an empty object.

Output ONLY valid JSON in this exact format:
{{
    "intent": "chat",
    "facts": {{"name": "Almighty", "city": "Bangalore"}}
}}"""
        
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        response_text = resp.content.strip()
        # Clean markdown code blocks if the LLM adds them
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        try:
            parsed = json.loads(response_text)
            intent = parsed.get("intent", "chat").lower()
            facts = parsed.get("facts", {})
            
            # Save extracted facts to Long Term Memory
            if self.memory_manager and facts and isinstance(facts, dict):
                user_id = state.get("user_id")
                for key, value in facts.items():
                    self.memory_manager.save_long_term_fact(user_id, key, value)
                    print(f"[Memory] Saved fact for {user_id}: {key} = {value}")
                    
        except json.JSONDecodeError:
            # Fallback if LLM didn't return JSON
            print(f"[Intent Error] Failed to parse JSON: {response_text}")
            if "data_analysis" in response_text.lower():
                intent = "data_analysis"
            elif "graph_search" in response_text.lower():
                intent = "graph_search"
            elif "search" in response_text.lower():
                intent = "search"
            else:
                intent = "chat"
                
        # Fallback for weird intent strings
        valid_intents = ["data_analysis", "graph_search", "search", "chat"]
        if intent not in valid_intents:
            intent = "chat"
        
        await streamer.emit_node_completed('intent_analyzer', get_metrics(start_time, locals().get('resp')))
        return {"intent": intent}
