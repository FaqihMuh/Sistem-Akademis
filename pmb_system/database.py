from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

def get_database_url():
    # Check if we're in a test environment
    if os.getenv("TESTING", "").lower() in ("1", "true", "yes"):
        return "sqlite:///:memory:"
    # Check if DATABASE_URL is set in environment (for production)
    env_db_url = os.getenv("DATABASE_URL")
    if env_db_url:
        return env_db_url
    # Default to SQLite for local development
    return "sqlite:///./pmb_local.db"

# Database URL - using environment variable, defaulting to SQLite
DATABASE_URL = get_database_url()

# Check if we're using SQLite or PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()