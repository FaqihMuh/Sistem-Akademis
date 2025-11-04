from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import OperationalError
import time
import random
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
    engine = create_engine(
        DATABASE_URL, 
        connect_args={
            "check_same_thread": False,
            "timeout": 15,  # Increase timeout for locked database
        },
        poolclass=StaticPool,  # Use StaticPool for SQLite to avoid locking issues
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        echo=False,  # Set to True to see SQL queries for debugging
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def commit_with_retry(db, max_retries=5, base_delay=0.1, max_delay=1.0, backoff_factor=2):
    """
    Commit database transaction with retry logic for SQLite locking issues
    """
    for attempt in range(max_retries + 1):
        try:
            db.commit()
            return  # Success, exit the function
        except OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries:
                # Calculate delay with exponential backoff and jitter
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)  # Add small jitter
                actual_delay = delay + jitter
                
                print(f"Database locked during commit, retrying in {actual_delay:.2f}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(actual_delay)
            else:
                raise e
    # If we get here, we've exhausted retries
    raise OperationalError("Database commit failed after retries", [], "Database is still locked after maximum retries")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()