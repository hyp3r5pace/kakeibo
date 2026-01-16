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
    

def create_expense(user_id, amount, expense_type, system_category_id, user_category_id, description, date):
    """
    Create a new expense
    
    :param user_id: ID of user creating expense
    :param amount: Expense amount (must be > 0)
    :param expense_type: 'expense' or 'income'
    :param system_category_id: ID from system_categories (nullable)
    :param user_category_id: ID from user_categories (nullable)
    :param description: Optional description
    :param date: Date of expense (YYYY-MM-DD format)
    :return: New expense ID if successful, None if failed
    """

    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO expenses 
                (user_id, amount, type, system_category_id, user_category_id, description, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, amount, expense_type, system_category_id, user_category_id, description, date)
            )
            conn.commit()
            expense_id = cursor.lastrowid
            print(f"Expense created successfully with ID: {expense_id}")
            return expense_id
    except Exception as e:
        print(f"Expense creation failed: {e}")
        return None
        

def get_user_expenses(user_id, start_date=None, end_date=None, 
                      system_category_id=None, user_category_id=None, 
                      expense_type=None):

    with get_db_connection() as conn:
        # Build WHERE dynamically
        where_conditions = ["e.user_id = ?"]
        params = [user_id]
        
        if start_date:
            where_conditions.append("e.date >= ?")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("e.date <= ?")
            params.append(end_date)
        
        if system_category_id:
            where_conditions.append("e.system_category_id = ?")
            params.append(system_category_id)
        
        if user_category_id:
            where_conditions.append("e.user_category_id = ?")
            params.append(user_category_id)
        
        if expense_type:
            where_conditions.append("e.type = ?")
            params.append(expense_type)
        
        where_clause = " AND ".join(where_conditions)
        
        # Query filters first, then joins
        query = f"""
            SELECT 
                e.id,
                e.user_id,
                e.amount,
                e.type,
                e.system_category_id,
                e.user_category_id,
                e.description,
                e.date,
                e.created_at,
                sc.display_name as system_category_name,
                uc.display_name as user_category_name
            FROM expenses e
            LEFT JOIN system_categories sc ON e.system_category_id = sc.id
            LEFT JOIN user_categories uc ON e.user_category_id = uc.id
            WHERE {where_clause}
            ORDER BY e.date DESC, e.created_at DESC
        """
        
        expenses = conn.execute(query, params).fetchall()
        return [dict(expense) for expense in expenses]

def get_expense_by_id(expense_id, user_id):
    """
    Get a specific expense by ID
    
    :param expense_id: Expense ID
    :param user_id: User ID (to verify ownership)
    :return: Expense record or None if not found
    """
    with get_db_connection() as conn:
        expense = conn.execute(
            """SELECT 
                e.id,
                e.user_id,
                e.amount,
                e.type,
                e.system_category_id,
                e.user_category_id,
                e.description,
                e.date,
                e.created_at,
                sc.display_name as system_category_name,
                uc.display_name as user_category_name
            FROM expenses e
            LEFT JOIN system_categories sc ON e.system_category_id = sc.id
            LEFT JOIN user_categories uc ON e.user_category_id = uc.id
            WHERE e.id = ? AND e.user_id = ?""",
            (expense_id, user_id)
        ).fetchone()
        
        return dict(expense) if expense else None


def update_expense(expense_id, user_id, amount=None, expense_type=None, 
                   system_category_id=None, user_category_id=None, 
                   description=None, date=None):
    """
    Update an expense
    
    :param expense_id: Expense ID to update
    :param user_id: User ID (to verify ownership)
    :param amount: New amount (optional)
    :param expense_type: New type (optional)
    :param system_category_id: New system category (optional)
    :param user_category_id: New user category (optional)
    :param description: New description (optional)
    :param date: New date (optional)
    :return: True if successful, False if failed
    """
    try:
        with get_db_connection() as conn:
            # Build UPDATE query dynamically
            updates = []
            params = []
            
            if amount is not None:
                updates.append("amount = ?")
                params.append(amount)
            
            if expense_type is not None:
                updates.append("type = ?")
                params.append(expense_type)
            
            if system_category_id is not None:
                updates.append("system_category_id = ?")
                params.append(system_category_id)
            
            if user_category_id is not None:
                updates.append("user_category_id = ?")
                params.append(user_category_id)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if date is not None:
                updates.append("date = ?")
                params.append(date)
            
            if not updates:
                print("No fields to update")
                return False
            
            # Execute update with ownership verification
            query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            params.extend([expense_id, user_id])
            
            result = conn.execute(query, params)
            conn.commit()
            
            # Check if any rows were updated
            if result.rowcount == 0:
                print(f"Expense {expense_id} not found or doesn't belong to user {user_id}")
                return False
            
            print(f"Expense {expense_id} updated successfully")
            return True
            
    except Exception as e:
        print(f"Expense update failed: {e}")
        return False

def delete_expense(expense_id, user_id):
    """
    Delete an expense
    
    :param expense_id: Expense ID to delete
    :param user_id: User ID (to verify ownership)
    :return: True if successful, False if failed
    """
    try:
        with get_db_connection() as conn:
            # Verify expense exists and belongs to user before deleting
            result = conn.execute(
                "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                (expense_id, user_id)
            )
            conn.commit()
            
            if result.rowcount == 0:
                print(f"Expense {expense_id} not found or doesn't belong to user {user_id}")
                return False
            
            print(f"Expense {expense_id} deleted successfully")
            return True        
    except Exception as e:
        print(f"Expense deletion failed: {e}")
        return False

if __name__ == "__main__":
    init_db()

