# database.py
import sqlite3
import os
from datetime import date
import time

def get_db_connection():
    """
    Create a connection to the SQLite database
    
    :return: Database connection with row_factory set to sqlite3.Row
    """
    db_path = os.path.join(os.path.dirname(__file__), 'expenses.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """
    Initialize the database with schema from schema.sql
    """
    with get_db_connection() as conn:
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        print("Database initialized successfully!")

# ==================== USER FUNCTIONS ====================

def create_user(email, password_hash, first_name, last_name):
    """
    Create a new user
    
    :param email: User's email address
    :param password_hash: Bcrypt hashed password
    :param first_name: User's first name
    :param last_name: User's last name
    :return: New user ID
    :raises sqlite3.IntegrityError: If email already exists
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO users (email, password_hash, first_name, last_name)
               VALUES (?, ?, ?, ?)""",
            (email, password_hash, first_name, last_name)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"User created successfully with ID: {user_id}")
        return user_id

def get_user_by_email(email):
    """
    Get user by email address
    
    :param email: Email address
    :return: User record as dict or None if not found
    """
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        return dict(user) if user else None

def get_user_by_id(user_id):
    """
    Get user by ID
    
    :param user_id: User ID
    :return: User record as dict or None if not found
    """
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        return dict(user) if user else None

# ==================== EXPENSE FUNCTIONS ====================

def create_expense(user_id, amount, expense_type, system_category_id=None, 
                   user_category_id=None, description="", date=date.today().isoformat()):
    """
    Create a new expense
    
    :param user_id: ID of user creating expense
    :param amount: Expense amount (must be > 0)
    :param expense_type: 'expense' or 'income'
    :param system_category_id: ID from system_categories (nullable)
    :param user_category_id: ID from user_categories (nullable)
    :param description: Optional description
    :param date: Date of expense (YYYY-MM-DD format)
    :return: New expense ID
    :raises sqlite3.IntegrityError: If constraints are violated
    """
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

def get_user_expenses(user_id, start_date=None, end_date=None, 
                      system_category_id=None, user_category_id=None, 
                      expense_type=None, page=1, per_page=20, sort_by='date', order='desc',
                      min_amount=None, max_amount=None):
    """
    Get all expenses for a user with optional filters
    
    :param user_id: User ID
    :param start_date: Optional start date filter (YYYY-MM-DD)
    :param end_date: Optional end date filter (YYYY-MM-DD)
    :param system_category_id: Optional system category filter
    :param user_category_id: Optional user category filter
    :param expense_type: Optional type filter ('expense' or 'income')
    :param page: Optional page number, determines offset
    :param per_page: Optional number of expenses per page
    :param sort_by: Column to sort the output by (default='date')
    :param order_by: what order to sort by (ascending or descending) (default='desc')
    :param min_amount: Optional Minimum amount to filter by
    :param max_amount: Optional Maximum amount to filter by
    :return: List of expense records
    """
    with get_db_connection() as conn:
        # Build WHERE conditions
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

        if min_amount is not None:
            where_conditions.append("e.amount >= ?")
            params.append(min_amount)
        
        if max_amount is not None:
            where_conditions.append("e.amount <= ?")
            params.append(max_amount)
        
        
        where_clause = " AND ".join(where_conditions)

        count_query = f"""
            SELECT COUNT(*) as total
            FROM expenses e
            WHERE {where_clause}
        """
        total_count = conn.execute(count_query, params).fetchone()['total']

        offset = (page-1) * per_page

        sort_column_map = {
            'date': 'e.date',
            'amount': 'e.amount',
            'created_at': 'e.created_at'
        }

        sort_column = sort_column_map[sort_by]
        order_direction = order.upper()

        order_by_clause = f"{sort_column} {order_direction}, e.id {order_direction}"
        
        # Query filters first, then joins
        data_query = f"""
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
            ORDER BY {order_by_clause}
            LIMIT ? OFFSET ?
        """
        
        params = params + [per_page, offset]

        start_time = time.time()
        expenses = conn.execute(data_query, params).fetchall()
        elapsed = time.time() - start_time

        if elapsed > 0.5:  # Log slow queries
            print(f"SLOW QUERY: sort_by={sort_by}, order={order}, time={elapsed:.2f}s")
    
        return {
            'expenses': [dict(expense) for expense in expenses],
            'total_count': total_count
        }

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
    :return: True if successful, False if not found
    """
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
            return False
        
        # Execute update with ownership verification
        query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        params.extend([expense_id, user_id])
        
        result = conn.execute(query, params)
        conn.commit()
        
        if result.rowcount == 0:
            return False
        
        print(f"Expense {expense_id} updated successfully")
        return True

def delete_expense(expense_id, user_id):
    """
    Delete an expense
    
    :param expense_id: Expense ID to delete
    :param user_id: User ID (to verify ownership)
    :return: True if successful, False if not found
    """
    with get_db_connection() as conn:
        result = conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id)
        )
        conn.commit()
        
        if result.rowcount == 0:
            return False
        
        print(f"Expense {expense_id} deleted successfully")
        return True

# ==================== CATEGORY FUNCTIONS ====================

def get_system_categories():
    """
    Get all system categories

    :return List of system category records
    """
    with get_db_connection() as conn:
        categories = conn.execute(
            """SELECT
                id,
                name,
                display_name
            FROM system_categories
            ORDER BY display_name"""
        ).fetchall()
        return [dict(cat) for cat in categories]

def get_user_categories(user_id):
    """
    Get all custom categories for a user
    
    :param user_id: User ID
    :return: List of user category records
    """
    with get_db_connection() as conn:
        categories = conn.execute(
            """SELECT 
                id,
                user_id,
                name,
                display_name,
                created_at
            FROM user_categories
            WHERE user_id = ?
            ORDER BY display_name""",
            (user_id,)
        ).fetchall()
        return [dict(cat) for cat in categories]

def create_user_category(user_id, name, display_name):  # Rename to match other functions
    """
    Create a custom user category
    
    :param user_id: User ID
    :param name: Category name (uppercase, normalized)
    :param display_name: Display name (as user typed it)
    :return: New category ID
    :raises sqlite3.IntegrityError: If category already exists
    """
    with get_db_connection() as conn:
        # Check if this name exists in system categories
        system_exists = conn.execute(
            "SELECT id FROM system_categories WHERE name = ?",
            (name,)
        ).fetchone()

        if system_exists:
            raise sqlite3.IntegrityError(
                f"Category '{name}' already exists as a system category"
            )
        
        # Check if user already has this category
        user_exists = conn.execute(
            "SELECT id FROM user_categories WHERE user_id = ? AND name = ?",
            (user_id, name)
        ).fetchone()

        if user_exists:
            raise sqlite3.IntegrityError(
                f"User already has category '{name}'"
            )
        
        # Create category
        cursor = conn.execute(
            """INSERT INTO user_categories (user_id, name, display_name)
            VALUES (?, ?, ?)""",
            (user_id, name, display_name)
        )
        conn.commit()
        category_id = cursor.lastrowid
        print(f"User category created successfully with ID: {category_id}")
        return category_id        
    
def delete_user_category(category_id, user_id):
    """
    Delete a user's custom category
    
    :param category_id: Category ID to delete
    :param user_id: User ID (to verify ownership)
    :return: True if successful, False if failed
    """
    with get_db_connection() as conn:
        # Verify category exists and belongs to user
        result = conn.execute(
            "DELETE FROM user_categories WHERE id = ? AND user_id = ?",
            (category_id, user_id)
        )
        conn.commit()

        if result.rowcount == 0:
            print(f"Category {category_id} not found or doesn't belong to user {user_id}")
            return False
        print(f"User category {category_id} deleted successfully")
        return True
    

if __name__ == "__main__":
    init_db()

