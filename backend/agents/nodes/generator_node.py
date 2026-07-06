import time
import json
import os
from agents.utils import get_metrics
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agents.state import AgentState, streamer

class GeneratorNode:
    def __init__(self, llm, mongo_memory_manager, token_manager, vector_memory_manager=None):
        self.llm = llm
        self.mongo_memory = mongo_memory_manager
        self.vector_memory = vector_memory_manager
        self.token_manager = token_manager
        self.master_metadata_path = os.path.join(os.getcwd(), "data", "master_chunk_metadata.json")

    def _get_indexed_files_summary(self) -> str:
        """Read the master metadata JSON and return a concise list of indexed files."""
        try:
            if not os.path.exists(self.master_metadata_path):
                return "No files have been ingested yet."
            with open(self.master_metadata_path, "r") as f:
                master = json.load(f)
            if not master:
                return "No files have been ingested yet."
            # Aggregate by file_name
            file_groups = {}
            for v in master.values():
                fname = v.get("file_name", "Unknown")
                ftype = v.get("type", "unstructured")
                if fname not in file_groups:
                    file_groups[fname] = ftype
            lines = [f"- {fname} ({ftype})" for fname, ftype in file_groups.items()]
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading index: {e}"

    async def __call__(self, state: AgentState):
        start_time = time.time()
        await streamer.emit_node_active('generator_agent', 'Running generator...')
        user_id = state.get("user_id", "default_user")
        session_id = state.get("session_id", "default_session")
        
        # Build System Prompt with Long-Term Memory and Retrieved Context
        query = state.get("translated_query", state["messages"][-1].content)
        facts = []
        if self.vector_memory:
            facts = self.vector_memory.search_memory(user_id, query, top_k=5)
            
        indexed_files = self._get_indexed_files_summary()
        
        sys_prompt = (
            "You are an intelligent enterprise AI assistant. Your primary goal is to answer the user's "
            "query conversationally and directly, addressing their specific intent.\n\n"
            "CRITICAL GUARDRAIL: You MUST ONLY answer questions based on the provided retrieved external context, "
            "user facts, or the Indexed File Inventory below. "
            "If the answer cannot be deduced from the provided context, you must politely refuse to answer and state that the query is outside your knowledge base. "
            "Do NOT use your pre-trained knowledge to answer questions.\n\n"
            f"Indexed File Inventory (all files available in the knowledge base):\n{indexed_files}\n\n"
        )
        if facts:
            sys_prompt += "User Facts (Relevant personalized context):\n" + "\n".join([f"- {f}" for f in facts]) + "\n\n"
            
        session_summary = self.mongo_memory.get_session_summary(session_id)
        if session_summary:
            sys_prompt += f"Running Conversation Summary (Past context):\n{session_summary}\n\n"
            
        if state.get("pandas_context"):
            sys_prompt += (
                f"Retrieved Tabular Data Context:\n"
                f"{state['pandas_context']}\n\n"
            )
            
        if state.get("context"):
            sys_prompt += (
                f"Retrieved External Context (Relevance={state.get('is_relevant')}):\n"
                f"{state['context']}\n\n"
                "CRITICAL INSTRUCTION: Do NOT just blindly copy-paste or dump the retrieved context. "
                "Synthesize the context to answer the specific question or intent of the user. "
                "If the context does not contain the answer, say so politely."
            )
            
        sys_msg = SystemMessage(content=sys_prompt)
        
        # Token Optimization (Only include last 3 messages to prevent bloat)
        messages_dicts = [{"role": "system", "content": sys_msg.content}]
        recent_messages = state["messages"][-3:]
        for msg in recent_messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            messages_dicts.append({"role": role, "content": msg.content})
            
        optimized_dicts, opt_stats = self.token_manager.optimize_messages(messages_dicts)
        
        optimized_msgs = []
        for d in optimized_dicts:
            if d["role"] == "system": optimized_msgs.append(SystemMessage(content=d["content"]))
            elif d["role"] == "user": optimized_msgs.append(HumanMessage(content=d["content"]))
            else: optimized_msgs.append(AIMessage(content=d["content"]))

            
        response = await self.llm.ainvoke(optimized_msgs)
        
        await streamer.emit_node_completed('generator_agent', get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res')))
        return {"messages": [response]}
