from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.connection_manager import ConnectionManager
from app.database import engine, Base, SessionLocal
from app.models import User, Room, UserRoom, Message

app = FastAPI()
manager = ConnectionManager()
Base.metadata.create_all(bind = engine)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message was sent: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("Someone has left the chat")
