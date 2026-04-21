from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.connection_manager import ConnectionManager
from app.database import engine, Base, SessionLocal
from app.models import User, Room, UserRoom, Message
from app.routes import router

app = FastAPI()

# Create all database tables on startup if they don't already exist
Base.metadata.create_all(bind = engine)

# Register all routes defined in routes.py
app.include_router(router)
