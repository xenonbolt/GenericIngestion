from fastapi import APIRouter
from pydantic import BaseModel
from agents.state import streamer
from auth.audit_manager import audit_manager
from api.dependencies import chatbot, memory_manager
from monitoring.observability import obs_manager

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

@router.post("/chat")
async def chat(request: ChatRequest):
    obs_manager.capture_event(request.user_id, "chat_message_received", {"session_id": request.session_id})
    audit_manager.log_action(request.user_id, "CHAT_MESSAGE_SENT", f"Session: {request.session_id}")
    
    await streamer.broadcast({
        "type": "state_transition",
        "node": "START",
        "message": f"Received message from {request.user_id}"
    })
    
    from memory.cache_manager import cache_manager
    
    # Bypass cache for dynamic customer analysis
    if request.message.startswith("ANALYZE_CUSTOMER:"):
        cached_reply = None
    else:
        cached_reply = cache_manager.get_cached_answer(request.message)
    
    if cached_reply:
        response_text = cached_reply
        await streamer.broadcast({
            "type": "state_transition",
            "node": "END",
            "message": "Served from Cache"
        })
    else:
        response_text = await chatbot.invoke(request.session_id, request.user_id, request.message)
        if not request.message.startswith("ANALYZE_CUSTOMER:"):
            cache_manager.set_cached_answer(request.message, response_text)
        await streamer.broadcast({
            "type": "state_transition",
            "node": "END",
            "message": "Finished processing message"
        })
        
    # Save the conversation turn to the permanent MongoDB session
    memory_manager.add_message(request.session_id, request.user_id, "user", request.message)
    memory_manager.add_message(request.session_id, request.user_id, "assistant", response_text)
    
    await streamer.broadcast({
        "type": "trace_completed"
    })
    
    return {"reply": response_text}

@router.get("/chat/sessions/{user_id}")
async def get_sessions(user_id: str):
    sessions = memory_manager.get_user_sessions(user_id)
    return {"sessions": sessions}

@router.get("/chat/history/{session_id}")
async def get_history(session_id: str):
    messages = memory_manager.get_messages(session_id)
    return {"messages": messages}

@router.delete("/chat/history/{session_id}")
async def delete_history(session_id: str):
    memory_manager.delete_session(session_id)
    return {"status": "success", "message": "Session deleted"}
