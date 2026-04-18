from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.connection_manager import ConnectionManager
from app.database import engine, Base, SessionLocal
from app.models import User, Room, UserRoom, Message
from app.routes import router

app = FastAPI()
Base.metadata.create_all(bind = engine)
app.include_router(router)


