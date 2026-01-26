import pytest
import sqlite3
import os
import sys
import bcrypt
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
import database

@pytest.fixture
def app():
    """
    Create flask app configured for testing
    """
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'

    return flask_app

@pytest.fixture
def client(app):
    """
    return flask test client
    """
    return app.test_client()

@pytest.fixture
def test_db(monkeypatch):
    """
    Create in-memory test database with schema
    
    This gives each test a fresh, isolated database.
    Database is automatically destroyed after test completes.
    
    Usage in tests:
        def test_create_user(test_db):
            conn = test_db
            # ... use conn to test database functions
    """
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Load schema
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())

    def mock_db_connection():
        return conn

    monkeypatch.setattr(database, 'get_db_connection', mock_db_connection)
    
    yield conn
    
    # Cleanup (automatically happens)
    conn.close()

@pytest.fixture
def sample_user():
    def _user(email="test@example.com", password="password123", first_name="John", last_name="Doe"):
        """
        Sample user data for testing
        
        Usage in tests:
            def test_register(client, sample_user):
                response = client.post('/register', json=sample_user)
                assert response.status_code == 201
        """
        return {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name
        }
    return _user


@pytest.fixture
def insert_test_user(test_db, sample_user):
    """
    This creates a sample test user in the DB
    """
    user = sample_user()
    password_hash = bcrypt.hashpw(user['password'].encode(), bcrypt.gensalt())

    cursor = test_db.execute(
        """
        INSERT INTO users (email, password_hash, first_name, last_name)
        VALUES (?, ?, ?, ?)""",
        (user['email'], password_hash, user["first_name"], user["last_name"])
    )
    test_db.commit()

    yield cursor.lastrowid


@pytest.fixture
def sample_expense():
    """
    Sample data for expense
    """
    def _expense(amount = 50, expense_type = "expense", system_category_id = None, user_category_id = None, description="Text expense", curr_date = date.today().isoformat()):
        return {"amount" : amount,
        "expense_type": expense_type,
        "system_category_id": None,
        "user_category_id": None,
        "description" : description,
        "curr_date": curr_date
        }
    
    return _expense

@pytest.fixture
def insert_test_expense(test_db, insert_test_user, sample_expense):
    """
    This inserts a test expense in the DB
    """
    expense = sample_expense()
    cursor = test_db.execute(
        """INSERT INTO expenses 
            (user_id, amount, type, system_category_id, user_category_id, description, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (insert_test_user, *expense.values())
    )
    test_db.commit()

    yield (cursor.lastrowid, insert_test_user)

@pytest.fixture
def insert_test_category(test_db, insert_test_user):
    def _insert_test_category(categories=["test category"]):
        """
        fixture to create a new user category
        """
        category_id_list = []
        for cat in categories:
            cursor = test_db.execute(
                """INSERT INTO user_categories (user_id, name, display_name)
                   VALUES (?, ?, ?)""",
                   (insert_test_user, cat.strip().upper().replace(' ', '_'), cat.strip())
            )
            category_id_list.append(cursor.lastrowid)
        test_db.commit()

        return (category_id_list, insert_test_user)
    return _insert_test_category


@pytest.fixture
def insert_test_multiple_expenses(test_db, insert_test_user):
    def insert_test_expenses(num_expense = 50):
        """
        Fixture to create multiple expenses
        
        :param num_expense = number of expenses (default: 50)
        """
        data = [(insert_test_user, 100+i, 'expense', None, None, "", date.today().isoformat()) for i in range(num_expense)]
        query = """
            INSERT INTO expenses
            (user_id, amount, type, system_category_id, user_category_id, description, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
        cursor = test_db.executemany(
            query,
            data
        )
        test_db.commit()
    
    return insert_test_expenses


