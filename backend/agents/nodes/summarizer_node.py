import time
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import AgentState, streamer

class SummarizerNode:
    def __init__(self, llm, memory_manager):
        self.llm = llm
        self.memory_manager = memory_manager

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('summarizer_agent', 'Summarizing chat history...')
        
        session_id = state.get("session_id", "default_session")
        
        # Get existing summary
        current_summary = self.memory_manager.get_session_summary(session_id)
        
        # We only want to summarize the most recent exchange (last User message and last Assistant message)
        # If there are fewer than 2 messages, we don't have a full exchange to summarize yet.
        if len(state["messages"]) >= 2:
            last_user_msg = state["messages"][-2].content if len(state["messages"]) > 1 else ""
            last_ai_msg = state["messages"][-1].content
            
            prompt = f"""You are an expert conversation summarizer.
Your goal is to progressively update a running summary of a conversation between a User and an AI Assistant.

Current Conversation Summary:
{current_summary if current_summary else "No summary exists yet."}

New Exchange to integrate:
User: {last_user_msg}
Assistant: {last_ai_msg}

Instructions:
1. Update the Current Summary to include the key points, facts, and conclusions from the New Exchange.
2. Keep the summary concise, objective, and focused on retaining important context for future interactions.
3. DO NOT output the conversation verbatim. DO NOT output any preamble like "Here is the summary".
4. Output ONLY the raw updated summary text.
"""
            
            resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
            new_summary = resp.content.strip()
            
            self.memory_manager.update_session_summary(session_id, new_summary)
        
        # Return empty dict because we don't need to update the main state (messages)
        # We just updated the MongoDB side effect.
        return {"messages": []}
