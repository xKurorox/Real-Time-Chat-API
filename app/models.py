from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False)
    email = Column(String, nullable = True, unique = True)
    messages = relationship("Message", back_populates = "users")
    rooms = relationship("Room", back_populates = "users", secondary = "user_rooms")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False, unique = True)
    users = relationship("User", back_populates = "rooms", secondary = "user_rooms")
    messages = relationship("Message", back_populates = "rooms")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key = True)
    text = Column(String, nullable = False)
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"), index = True)
    room_id = Column(Integer, ForeignKey("rooms.id"), index = True)
    users = relationship("User", back_populates = "messages")
    rooms = relationship("Room", back_populates = "messages")

class UserRoom(Base):
    __tablename__ = "user_rooms"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"), index = True)
    room_id = Column(Integer, ForeignKey("rooms.id"), index = True)
    join_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))