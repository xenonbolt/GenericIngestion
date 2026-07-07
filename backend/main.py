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

# Import Routers
from api.auth import router as auth_router
from api.admin import router as admin_router
from api.upload import router as upload_router
from api.snow import router as snow_router
from api.risk import router as risk_router

app = FastAPI(title="Enterprise Agentic AI Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(upload_router)
app.include_router(snow_router)
app.include_router(risk_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Universal Agentic Intelligence Platform API is running."}

