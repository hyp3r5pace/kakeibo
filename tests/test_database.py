import pytest
import bcrypt
from database import (create_user,
                      get_user_by_email,
                      get_user_by_id,
                      create_expense,
                      get_user_expenses,
                      get_expense_by_id,
                      update_expense,
                      delete_expense
                    )
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

    test_user = sample_user()
    user = get_user_by_id(insert_test_user)

    assert user["id"] is not None
    assert user["id"] > 0
    assert user["first_name"] == test_user['first_name']
    assert user["last_name"] == test_user["last_name"]
    assert user["email"] == test_user["email"]


def test_get_user_by_id_not_found():
    """
    Test retreiving user by ID which does not exist
    """
    user = get_user_by_id(5)
    assert user is None



# ======================= EXPENSES TEST ==========================

def test_create_valid_expense_for_existing_user(test_db, insert_test_user):
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


def test_get_user_expenses(insert_test_expense):
    """
    Test getting expense for a user
    """
    expense_id, user_id = insert_test_expense
    expense_list = get_user_expenses(user_id)

    assert len(expense_list) == 1
    
    stored_expense = expense_list[0]

    assert stored_expense['id'] == expense_id
    assert stored_expense["user_id"] == user_id


def test_get_expense_by_id(insert_test_expense):
    """
    Test for getting expense corresponding a specific expense ID and user ID
    """
    expense_id, user_id = insert_test_expense
    expense = get_expense_by_id(expense_id, user_id)
    
    assert expense is not None
    assert expense["id"] == expense_id
    assert expense["user_id"] == user_id


def test_get_expense_by_id_not_found(insert_test_user):
    """
    Test for getting expense corresponding a
    non existing expense ID and user ID 
    """
    expense = get_expense_by_id(10, insert_test_user)
    
    assert expense is None


def test_update_expense(test_db, insert_test_expense):
    """
    Test for updating an existing expense
    """
    expense_id, user_id = insert_test_expense
    success = update_expense(expense_id, user_id, 75, "income")

    assert success == True

    cursor = test_db.execute("SELECT * from expenses where id = ? and user_id = ?", (expense_id, user_id))
    expense = cursor.fetchone()

    assert expense["amount"] == 75
    assert expense["type"] == "income"

def test_update_expense_not_found(test_db, insert_test_user):
    """
    Test for updating an non existing expense
    """
    success = update_expense(10, insert_test_user, 75, "income")

    assert success == False

def test_delete_expense(test_db, insert_test_expense):
    """
    Test for deleting an existing expense
    """
    expense_id, user_id = insert_test_expense
    success = delete_expense(expense_id, user_id)

    assert success == True

    cursor = test_db.execute("SELECT * FROM expenses where id = ?", (expense_id,))
    expense = cursor.fetchone()
    
    assert expense is None


