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

def create_user(email, password_hash, first_name, last_name):
    """
    DB query to create a user profile
    
    :param email: email ID of the user
    :param password_hash: password hash of the user
    :return New user's ID if successful, None if failed
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (first_name, last_name, email, password_hash) VALUES (?,?,?,?)", (first_name, last_name, email, password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            print(f"User created successfully with ID: {user_id}")
            return user_id
    except sqlite3.IntegrityError as e:
        print(f"User creation failed - email already exists: {email}")
        return None
    except Exception as e:
        print(f"User creation failed with error: {e}")
        return None

def get_user_by_email(email):
    """
    Retrieve a user by their email address.
    
    :param email: User's email address
    :return: User row as dict-like object, or None if not found
    """
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email, )
        ).fetchone()
        return user
    
def get_user_by_id(user_id):
    """
    Retrieve a user by their ID.
    
    :param user_id: User's ID
    :return: User row as dict-like object, or None if not found
    """
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        return user
        



if __name__ == "__main__":
    init_db()

