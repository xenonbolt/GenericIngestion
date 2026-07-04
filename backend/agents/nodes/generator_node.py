from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agents.state import AgentState, streamer

class GeneratorNode:
    def __init__(self, llm, memory_manager, token_manager):
        self.llm = llm
        self.memory_manager = memory_manager
        self.token_manager = token_manager

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('generator_agent', 'Running generator...')
        user_id = state.get("user_id", "default_user")
        
        # Build System Prompt with Long-Term Memory and Retrieved Context
        facts = self.memory_manager.get_long_term_facts(user_id)
        sys_prompt = (
            "You are an intelligent enterprise AI assistant. Your primary goal is to answer the user's "
            "query conversationally and directly, addressing their specific intent.\n\n"
            "CRITICAL GUARDRAIL: You MUST ONLY answer questions based on the provided retrieved external context or user facts. "
            "If the answer cannot be deduced from the provided context, you must politely refuse to answer and state that the query is outside your knowledge base. "
            "Do NOT use your pre-trained knowledge to answer questions.\n\n"
        )
        if facts:
            sys_prompt += "User Facts (Personalized context):\n" + "\n".join([f"- {k}: {v}" for k, v in facts.items()]) + "\n\n"
            
        if state.get("context"):
            sys_prompt += (
                f"Retrieved External Context (Relevance={state.get('is_relevant')}):\n"
                f"{state['context']}\n\n"
                "CRITICAL INSTRUCTION: Do NOT just blindly copy-paste or dump the retrieved context. "
                "Synthesize the context to answer the specific question or intent of the user. "
                "If the context does not contain the answer, say so politely."
            )
            
        sys_msg = SystemMessage(content=sys_prompt)
        
        # Token Optimization
        messages_dicts = [{"role": "system", "content": sys_msg.content}]
        for msg in state["messages"]:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            messages_dicts.append({"role": role, "content": msg.content})
            
        optimized_dicts, opt_stats = self.token_manager.optimize_messages(messages_dicts)
        
        optimized_msgs = []
        for d in optimized_dicts:
            if d["role"] == "system": optimized_msgs.append(SystemMessage(content=d["content"]))
            elif d["role"] == "user": optimized_msgs.append(HumanMessage(content=d["content"]))
            else: optimized_msgs.append(AIMessage(content=d["content"]))

                
        response = await self.llm.ainvoke(optimized_msgs)
        
        # Save to short term memory
        if isinstance(state["messages"][-1], HumanMessage):
            self.memory_manager.add_message(state["session_id"], user_id, "user", state["messages"][-1].content)
        self.memory_manager.add_message(state["session_id"], user_id, "assistant", response.content)
        
        await streamer.emit_node_completed('generator_agent', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
        return {"messages": [response]}
