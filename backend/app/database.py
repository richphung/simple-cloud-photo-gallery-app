"""
Database configuration and session management for the Simple Cloud Photo Gallery App.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Database URL - using SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./photo_gallery.db")

# Create SQLAlchemy engine
# Using StaticPool for SQLite to handle concurrent access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=True  # Set to False in production
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database by creating all tables.
    """
    Base.metadata.create_all(bind=engine)

def reset_db():
    """
    Reset database by dropping and recreating all tables.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)



