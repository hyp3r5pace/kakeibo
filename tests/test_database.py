import pytest
import bcrypt
from database import create_user, get_user_by_email, get_user_by_id, create_expense
import sqlite3

def test_database_fixture_works(test_db):
    """
    Test that the test database fixture is working
    
    This is a simple sanity check to ensure:
    - In-memory database is created
    - Schema is loaded
    - We can query tables
    """
    cursor = test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    )
    result = cursor.fetchone()
    
    assert result is not None
    assert result['name'] == 'users'

def test_create_user(test_db):
    """
    Test creating a user in database
    """
    email = "test@example.com"
    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt())
    first_name = "John"
    last_name = "Doe"

    user_id = create_user(email, password_hash, first_name, last_name)

    assert user_id is not None
    assert user_id > 0

    cursor = test_db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    assert user is not None
    assert user['email'] == email
    assert user['first_name'] == first_name
    assert user['last_name'] == last_name

def test_get_user_by_email(test_db):
    """Test retrieving user by email"""
    # Arrange - Create a user first
    email = "test@example.com"
    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt())
    user_id = create_user(email, password_hash, "John", "Doe")
    
    # Act
    user = get_user_by_email(email)
    
    # Assert
    assert user is not None
    assert user['id'] == user_id
    assert user['email'] == email
    assert user['first_name'] == "John"

def test_get_user_by_email_not_found(test_db):
    """Test that getting non-existent user returns None"""
    # Act
    user = get_user_by_email("nonexistent@example.com")
    
    # Assert
    assert user is None

def test_get_user_by_id(sample_user, insert_test_user):
    """
    Test retreiving user by ID
    """
    user = get_user_by_id(insert_test_user)

    assert user["id"] is not None
    assert user["id"] > 0
    assert user["first_name"] == sample_user['first_name']
    assert user["last_name"] == sample_user["last_name"]
    assert user["email"] == sample_user["email"]


def test_get_user_by_id_not_found(sample_user):
    """
    Test retreiving user by ID which does not exist
    """
    user = get_user_by_id(5)
    assert user is None



# ======================= EXPENSES TEST ==========================

def test_create_valid_expense_for_existing_user(test_db, sample_user, insert_test_user):
    """
    Test creating a valid expense for a existing user
    """
    amount = 50
    expense_type = 'expense'
    
    expense_id = create_expense(insert_test_user, amount, expense_type)

    assert expense_id is not None
    assert expense_id  > 0

    cursor = test_db.execute("SELECT * from expenses where id = ?", (expense_id,))
    expense = cursor.fetchone()

    assert expense is not None
    assert expense["amount"] == amount
    assert expense["type"] == expense_type
    assert expense["system_category_id"] == None
    assert expense["description"] == ""


def test_create_valid_expense_for_invalid_user(test_db):
    """
    Test creating expense for an non existing user
    """
    amount = 50
    expense_type = 'expense'
    
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        create_expense(10, amount, expense_type)




