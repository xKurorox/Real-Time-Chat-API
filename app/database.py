from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base

# Connect to SQLite database file; check_same_thread=False allows FastAPI's threads to share the connection
engine = create_engine("sqlite:///./url.db", connect_args = {"check_same_thread": False})

# Factory for creating new database sessions
SessionLocal = sessionmaker(autocommit = False, bind = engine)

# Base class that all models inherit from so SQLAlchemy can track them
Base = declarative_base()

# Dependency injected into route functions — opens a session, yields it, then closes it when the request is done
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
