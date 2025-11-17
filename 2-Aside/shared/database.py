"""
2-Aside Platform - Shared Database Configuration
Provides database connection and session management for all microservices
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine
# For Azure SQL, use NullPool to avoid connection pooling issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    future=True
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    Call this during application startup.
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """
    Drop all tables - use with caution!
    Only for development/testing.
    """
    Base.metadata.drop_all(bind=engine)


# Event listener for SQL Server to set isolation level
@event.listens_for(engine, "connect")
def set_isolation_level(dbapi_conn, connection_record):
    """
    Set SQL Server transaction isolation level to READ COMMITTED
    to prevent dirty reads while allowing concurrent access.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
    cursor.close()
