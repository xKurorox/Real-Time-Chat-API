from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload
from app.database import get_db, Base, engine
from app.models import User, Room, UserRoom, Message
from typing import Optional
from app.pydantic_models import CreateUser, CreateRoom, JoinRoom, UserResponse, RoomResponse, MessageResponse
from app.connection_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "message":
                user = db.query(User).filter(User.id == data["user_id"]).first()
                if not user:
                    await websocket.send_json({"type": "error", "message": "User was not found"})
                    continue
                room = db.query(Room).filter(Room.id == data["room_id"]).first()
                if not room:
                    await websocket.send_json({"type": "error", "message": "Room was not found"})
                    continue
                new_message = Message(text = data["text"], user_id = data["user_id"], room_id = data["room_id"])
                db.add(new_message)
                db.commit()
                db.refresh(new_message)
                message_data = {"id": new_message.id,
                                "user_id": user.id,
                                "username": user.name,
                                "room_id": new_message.room_id,
                                "text": new_message.text,
                                "created_at": new_message.created_at.isoformat()
                                }  
                await manager.broadcast(message_data)
            elif data["type"] == "typing":
                user = db.query(User).filter(User.id == data["user_id"]).first()
                if not user:
                        await websocket.send_json({"type": "error", "message": "User was not found"})
                        continue
                typing_data = {"type": "typing", "username": user.name, "room_id": data["room_id"]}
                await manager.broadcast(typing_data, websocket)
            elif data["type"] == "join":
                user = db.query(User).filter(User.id == data["user_id"]).first()
                if not user:
                    await websocket.send_json({"type": "error", "message": "User was not found"})
                    continue
                manager.register_user(websocket, {"user_id": user.id, "username": user.name})
                presence_data = {"type": "presence", "username": user.name, "status": "online"}
                await manager.broadcast(presence_data)
            else:
                await websocket.send_json({"type": "error", "message": "Unknown event type"})
    except WebSocketDisconnect:
        user_info = manager.user_connections.get(websocket)
        manager.disconnect(websocket)
        if  user_info:
            presence_data = {"type": "presence", "username": user_info["username"], "status": "offline"}
            await manager.broadcast(presence_data)


@router.get("/rooms/{room_id}/messages", response_model = list[MessageResponse])
def get_messages(room_id: int, limit: int = 20, before: int = None, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code = 404, detail = "Room not found")
    messages = db.query(Message).filter(Message.room_id == room_id).options(joinedload(Message.users))
    if before:
        messages = messages.filter(Message.id < before)
    messages = messages.order_by(Message.id.desc()).limit(limit).all()
    return messages

@router.get("/rooms", response_model = list[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    list_rooms = db.query(Room).all()
    return list_rooms

@router.get("/rooms/{room_id}/members", response_model = list[UserResponse])
def get_room_members(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code = 404, detail = "Room not found")
    return room.users

@router.post("/users", response_model = UserResponse)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    user_name = db.query(User).filter(User.name == user.name).first()
    if user_name:
        raise HTTPException(status_code = 409, detail = "Username already taken")
    if user.email:
        user_email = db.query(User).filter(User.email == user.email).first()
        if user_email:
            raise HTTPException(status_code = 409, detail = "Email already in use")        
    new_user = User(name = user.name, email = user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/rooms", response_model = RoomResponse)
def create_room(room: CreateRoom, db: Session = Depends(get_db)):
    existing_room = db.query(Room).filter(Room.name == room.name).first()
    if existing_room:
        raise HTTPException(status_code = 409, detail = "Room name already taken")
    existing_user = db.query(User).filter(User.id == room.user_id).first()
    if not existing_user:
        raise HTTPException(status_code = 404, detail = "Not a valid user id")
    new_room = Room(name = room.name)
    db.add(new_room)
    db.flush()
    new_user_room = UserRoom(room_id = new_room.id, user_id = existing_user.id)
    db.add(new_user_room)
    db.commit()
    db.refresh(new_room)
    return new_room

@router.post("/rooms/{room_id}/members")
def new_room_member(user: JoinRoom, room_id: int, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user.user_id).first()
    if not existing_user:
        raise HTTPException(status_code = 404, detail = "User not found")
    existing_room = db.query(Room).filter(Room.id == room_id).first()
    if not existing_room:
        raise HTTPException(status_code = 404, detail = "Room not found")
    existing_user_room = db.query(UserRoom).filter(UserRoom.user_id == existing_user.id, UserRoom.room_id == existing_room.id).first()
    if existing_user_room:
        raise HTTPException(status_code = 409, detail = "User is already in room")
    new_room_member = UserRoom(room_id = existing_room.id, user_id = existing_user.id)
    db.add(new_room_member)
    db.commit()
    db.refresh(new_room_member)
    return {"message": f"{existing_user.name} has joined {existing_room.name} room"}
