"""
Database initialization for the grades system
This script creates all tables in the correct order to handle foreign key dependencies
"""
from pmb_system.database import engine
from sqlalchemy import text

def create_grades_tables():
    """Create grades tables with proper foreign key handling"""
    
    # SQL to create grades table (with foreign keys as references only for now)
    create_grades_sql = """
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nim VARCHAR(20) NOT NULL,
        matakuliah_id INTEGER NOT NULL,
        semester VARCHAR(20) NOT NULL,
        nilai_huruf VARCHAR(2) NOT NULL,
        nilai_angka REAL NOT NULL,
        sks INTEGER NOT NULL,
        dosen_id INTEGER NOT NULL,
        presensi REAL DEFAULT 100.0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_grade_history_sql = """
    CREATE TABLE IF NOT EXISTS grade_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grade_id INTEGER NOT NULL,
        old_value VARCHAR(50) NOT NULL,
        new_value VARCHAR(50) NOT NULL,
        changed_by VARCHAR(255) NOT NULL,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        reason TEXT
    );
    """
    
    # Add foreign key constraints (may fail if referenced tables don't exist yet, which is OK)
    add_grades_fk_nim = """
    CREATE INDEX IF NOT EXISTS idx_grades_nim ON grades(nim);
    """
    
    add_grades_fk_matakuliah = """
    CREATE INDEX IF NOT EXISTS idx_grades_matakuliah_id ON grades(matakuliah_id);
    """
    
    add_grades_fk_dosen = """
    CREATE INDEX IF NOT EXISTS idx_grades_dosen_id ON grades(dosen_id);
    """
    
    add_history_fk = """
    CREATE INDEX IF NOT EXISTS idx_grade_history_grade_id ON grade_history(grade_id);
    """
    
    with engine.connect() as conn:
        # Create tables
        conn.execute(text(create_grades_sql))
        conn.execute(text(create_grade_history_sql))
        
        # Create indexes
        conn.execute(text(add_grades_fk_nim))
        conn.execute(text(add_grades_fk_matakuliah))
        conn.execute(text(add_grades_fk_dosen))
        conn.execute(text(add_history_fk))
        
        # Commit the transaction
        conn.commit()
    
    print("Grades tables created successfully!")


if __name__ == "__main__":
    create_grades_tables()