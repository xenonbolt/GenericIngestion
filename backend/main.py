from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from dotenv import load_dotenv

import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler("logs/backend.log", maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()
import utils.security 

from agents.state import streamer
from graph.networkx_store import kg_store

# Import Routers
from api.auth import router as auth_router
from api.admin import router as admin_router
from api.chat import router as chat_router
from api.upload import router as upload_router
from api.dashboard import router as dashboard_router

app = FastAPI(title="Enterprise Agentic AI Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(dashboard_router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Universal Agentic Intelligence Platform API is running."}

@app.get("/graph")
def get_graph():
    return kg_store.get_graph_data_for_ui()

@app.websocket("/ws/agent-stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    streamer.add_queue(queue)
    try:
        while True:
            event = await queue.get()
            await websocket.send_text(event)
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        streamer.remove_queue(queue)
