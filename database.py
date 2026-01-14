import sqlite3
DATABASE_NAME = 'expenses.db'

def get_db_connection():
    """
    Create and return a database connection
    Enables foreign key support and sets row factory for dict like access    
    """
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database by executing schema.sql
    This creates all tables and inserts seed data
    """
    try:
        with get_db_connection() as conn:
            with open('schema.sql', 'r') as f:
                conn.executescript(f.read())
        print('Database initialized successfully!')
    except Exception as e:
        print(f'Database initialization error: {e}')

if __name__ == "__main__":
    init_db()

