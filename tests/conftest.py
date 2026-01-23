import pytest
import sqlite3
import os
import sys
import bcrypt

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
    """
    Sample user data for testing
    
    Usage in tests:
        def test_register(client, sample_user):
            response = client.post('/register', json=sample_user)
            assert response.status_code == 201
    """
    return {
        "email": "test@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe"
    }


@pytest.fixture
def insert_test_user(test_db, sample_user):
    """
    This creates a sample test user in the DB
    """
    password_hash = bcrypt.hashpw(sample_user['password'].encode(), bcrypt.gensalt())

    cursor = test_db.execute(
        """
        INSERT INTO users (email, password_hash, first_name, last_name)
        VALUES (?, ?, ?, ?)""",
        (sample_user['email'], password_hash, sample_user["first_name"], sample_user["last_name"])
    )

    return cursor.lastrowid
