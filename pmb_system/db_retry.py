"""
Database retry utility for handling SQLite locking issues
"""
import time
import random
from functools import wraps
from sqlalchemy.exc import OperationalError


def retry_db_operation(max_retries=5, base_delay=0.1, max_delay=1.0, backoff_factor=2):
    """
    Decorator to retry database operations that fail due to SQLite locking issues
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e).lower() and attempt < max_retries:
                        # Calculate delay with exponential backoff and jitter
                        delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                        jitter = random.uniform(0, delay * 0.1)  # Add small jitter
                        actual_delay = delay + jitter
                        
                        print(f"Database locked, retrying in {actual_delay:.2f}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(actual_delay)
                        
                        last_exception = e
                    else:
                        raise e
            # If we get here, we've exhausted retries
            raise last_exception
        return wrapper
    return decorator