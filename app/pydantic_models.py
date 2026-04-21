from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Request body for creating a new user
class CreateUser(BaseModel):
    name: str
    email: Optional[str] = None  # email is optional

# Request body for creating a new room
class CreateRoom(BaseModel):
    name: str
    user_id: int  # the user creating the room; they are automatically added as a member

# Request body for adding a user to a room
class JoinRoom(BaseModel):
    user_id: int

# Response shape returned when a user is created or fetched
class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None

    class Config:
        from_attributes = True  # allows Pydantic to read data from SQLAlchemy model instances

# Response shape returned for a message
class MessageResponse(BaseModel):
    id: int
    text: str
    user_id : int
    users: UserResponse  # nested user object so the caller gets the username alongside the message
    room_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Response shape returned when a room is created or fetched
class RoomResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
