from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class QueryTranslatorNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('query_translator', 'Running translator...')
        latest_msg = state["messages"][-1].content
        prompt = (
            "You are a query translator. The user just said: '{query}'.\n"
            "If the query is vague (like 'Get me the report' or 'Summarize the data'), "
            "translate it into a highly explicit and precise search instruction. "
            "If it's already precise or just conversational, return it as is. "
            "Output ONLY the translated query text, nothing else."
        ).format(query=latest_msg)
        
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        translated = resp.content.strip()
        
        await streamer.emit_node_completed('query_translator', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
        return {"translated_query": translated}
