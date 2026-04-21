from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

# Represents a registered user
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False)
    email = Column(String, nullable = True, unique = True)  # email is optional but must be unique
    messages = relationship("Message", back_populates = "users")
    rooms = relationship("Room", back_populates = "users", secondary = "user_rooms")  # many-to-many via user_rooms

# Represents a chat room
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False, unique = True)
    users = relationship("User", back_populates = "rooms", secondary = "user_rooms")  # many-to-many via user_rooms
    messages = relationship("Message", back_populates = "rooms")

# Represents a single chat message
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key = True)
    text = Column(String, nullable = False)
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))  # auto-set to UTC time on insert
    user_id = Column(Integer, ForeignKey("users.id"), index = True)
    room_id = Column(Integer, ForeignKey("rooms.id"), index = True)
    users = relationship("User", back_populates = "messages")
    rooms = relationship("Room", back_populates = "messages")

# Join table tracking which users belong to which rooms
class UserRoom(Base):
    __tablename__ = "user_rooms"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"), index = True)
    room_id = Column(Integer, ForeignKey("rooms.id"), index = True)
    join_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))  # records when the user joined
