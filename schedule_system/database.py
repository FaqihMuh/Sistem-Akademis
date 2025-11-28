from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import time
import random
import os

# Import the database configuration from PMB system to ensure consistent database usage across all modules
from pmb_system.database import engine, Base, get_database_url

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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