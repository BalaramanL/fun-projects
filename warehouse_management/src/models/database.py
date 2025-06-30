"""
Database module for the warehouse management system.
Provides SQLAlchemy database engine and session management.
"""
import os
import logging
from typing import Any, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import DATABASE_URI

logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
Base = declarative_base()

# Create database engine
engine = create_engine(
    DATABASE_URI,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for debugging SQL queries
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Enable SQLite foreign key support
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """
    Enable SQLite foreign key support and load SpatiaLite extension.
    
    Args:
        dbapi_connection: SQLite connection
        connection_record: Connection record
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # Try to load SpatiaLite extension if available
    try:
        cursor.execute("SELECT load_extension('mod_spatialite')")
    except Exception as e:
        logger.warning(f"Could not load SpatiaLite extension: {e}")
    
    cursor.close()

def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Session: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize database by creating all tables.
    """
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def drop_db() -> None:
    """
    Drop all database tables.
    Use with caution!
    """
    logger.warning("Dropping all database tables")
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database tables dropped successfully")
