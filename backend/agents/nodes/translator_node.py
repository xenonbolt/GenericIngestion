from langchain_core.messages import HumanMessage
from agents.state import AgentState, streamer

class QueryTranslatorNode:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('query_translator', 'Running translator...')
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in state["messages"][-5:-1]])
        latest_msg = state["messages"][-1].content
        prompt = (
            f"You are a query translator. Here is the recent chat history:\n{history_str}\n\n"
            f"The user just said: '{latest_msg}'.\n"
            "If the query is vague, context-dependent (like 'third user'), or needs coreference resolution, "
            "translate it into a highly explicit and precise standalone search instruction. "
            "If it's already precise, return it as is. "
            "Output ONLY the translated query text, nothing else."
        )
        
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        translated = resp.content.strip()
        
        await streamer.emit_node_completed('query_translator', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
        return {"translated_query": translated}
