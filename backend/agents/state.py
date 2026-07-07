import json
import asyncio
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class EventStreamer:
    def __init__(self):
        self.queues = []
    def add_queue(self, queue: asyncio.Queue):
        self.queues.append(queue)
    def remove_queue(self, queue: asyncio.Queue):
        if queue in self.queues:
            self.queues.remove(queue)
    async def broadcast(self, event: dict):
        for queue in self.queues:
            await queue.put(json.dumps(event))

    async def emit_node_active(self, node_id: str, action: str):
        await self.broadcast({
            "type": "node_active",
            "nodeId": node_id,
            "action": action
        })
        
    async def emit_node_completed(self, node_id: str, metrics: dict = None):
        payload = {
            "type": "node_completed",
            "nodeId": node_id
        }
        if metrics:
            payload["metrics"] = metrics
        await self.broadcast(payload)

streamer = EventStreamer()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    user_id: str
    translated_query: str
    intent: str
    tasks: list[str]
    pandas_tasks: list[str]
    use_vector: bool
    use_pandas: bool
    context: str
    pandas_context: str
    networkx_answer: str
    kuzu_answer: str
    is_relevant: bool
    retrieval_attempts: int
    target_customer_id: str
    ticket_analysis: str
    transcript_analysis: str
