import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

logger = logging.getLogger("criminal_network.database")

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create Engine
engine = None
try:
    # Handle SQLite fallback for testing environments if specified
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

def get_db() -> Generator:
    """Dependency for obtaining database sessions per request."""
    if SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_connection() -> bool:
    """Verify live connection to PostgreSQL database."""
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False
