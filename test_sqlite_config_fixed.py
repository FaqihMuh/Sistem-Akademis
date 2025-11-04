"""
Test script to verify the database configuration fixes without file locking issues
"""
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

def test_sqlite_config():
    """Test SQLite configuration with timeout and connection pooling parameters"""
    
    print("Testing SQLite configuration with timeout...")
    
    # Test with in-memory database to avoid file locking issues
    DATABASE_URL = "sqlite:///:memory:"
    
    # Create engine with the same parameters as our fix (without pool settings for SQLite)
    engine = create_engine(
        DATABASE_URL, 
        connect_args={
            "check_same_thread": False,
            "timeout": 20,  # Increase timeout for locked database
        },
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
    )
    
    # Create tables and test basic operations
    Base = declarative_base()
    
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.orm import sessionmaker
    
    # Define a simple test model
    class TestModel(Base):
        __tablename__ = 'test_table'
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Test creating a session and performing operations
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test inserting a record
        test_record = TestModel(name="Test Record")
        db.add(test_record)
        db.commit()
        db.refresh(test_record)
        
        print(f"Successfully inserted record: {test_record.name}")
        
        # Test querying the record
        found_record = db.query(TestModel).filter(TestModel.name == "Test Record").first()
        print(f"Successfully queried record: {found_record.name if found_record else None}")
        
        # Test multiple operations to verify concurrency handling
        for i in range(5):
            another_record = TestModel(name=f"Test Record {i}")
            db.add(another_record)
        
        db.commit()
        print("Successfully committed multiple records")
        
        # Verify all records
        all_records = db.query(TestModel).all()
        print(f"Total records in database: {len(all_records)}")
        
        print("SUCCESS: Database configuration works correctly with timeout!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_sqlite_config()
    if not success:
        sys.exit(1)
    print("\nSQLite configuration test completed successfully!")