from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CreateUser(BaseModel):
    name: str
    email: Optional[str] = None

class CreateRoom(BaseModel):
    name: str
    user_id: int

class JoinRoom(BaseModel):
    user_id: int

class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    text: str
    user_id : int
    users: UserResponse
    room_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class RoomResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True