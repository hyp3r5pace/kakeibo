import pytest
import bcrypt
from database import *
import sqlite3
from datetime import date

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

    assert success

    cursor = test_db.execute("SELECT * from expenses where id = ? and user_id = ?", (expense_id, user_id))
    expense = cursor.fetchone()

    assert expense["amount"] == 75
    assert expense["type"] == "income"

def test_update_expense_not_found(test_db, insert_test_user):
    """
    Test for updating an non existing expense
    """
    success = update_expense(10, insert_test_user, 75, "income")

    assert not success

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


def test_get_user_expenses_pagination_first_page(test_db, insert_test_user, insert_test_multiple_expenses):
    """
    Test first page returns correct items
    """
    insert_test_multiple_expenses()

    result = get_user_expenses(insert_test_user, page=1, per_page=20)

    assert len(result['expenses']) == 20
    assert result['total_count'] == 50
    assert result['expenses'][-1]['id'] == 31

def test_get_user_expense_pagination_last_page(test_db, insert_test_user, insert_test_multiple_expenses):
    """
    Test last page returns correct items
    """
    insert_test_multiple_expenses(25)

    result = get_user_expenses(insert_test_user, page=2, per_page=20)

    assert len(result['expenses']) == 5
    assert result['total_count'] == 25
    assert result['expenses'][-1]['id'] == 1

def test_get_user_expenses_pagination_empty_page(test_db, insert_test_user, insert_test_multiple_expenses):
    """Test page beyond range returns empty"""
    
    insert_test_multiple_expenses(10)
    result = get_user_expenses(insert_test_user, page=5, per_page=20)

    assert len(result['expenses']) == 0
    assert result['total_count'] == 10

def test_get_user_expenses_pagination_with_filters(test_db, insert_test_user):
    """
    Test pagination works with filters
    """
    data = [(insert_test_user, 100+i, 'expense' if i%2 == 0 else 'income', None, None, "", date.today().isoformat()) for i in range(30)]
    query = """
        INSERT INTO expenses
        (user_id, amount, type, system_category_id, user_category_id, description, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)"""
    cursor = test_db.executemany(
        query,
        data
    )
    test_db.commit()

    result = get_user_expenses(
        insert_test_user,
        expense_type='expense',
        page=1,
        per_page=10
    )

    assert len(result['expenses']) == 10
    assert result['total_count'] == 15
    assert all(e['type'] == 'expense' for e in result['expenses'])


def test_get_user_expenses_pagination_order(test_db, insert_test_user):
    """
    Test results are ordered correctly
    """
    dates = ['2024-01-01', '2024-01-05', '2024-01-03']
    data = [(insert_test_user, 100+i, 'expense', None, None, "", expense_date) for i, expense_date in enumerate(dates)]
    query = """
        INSERT INTO expenses
        (user_id, amount, type, system_category_id, user_category_id, description, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)"""
    cursor = test_db.executemany(
        query,
        data
    )
    test_db.commit()

    result = get_user_expenses(insert_test_user, page=1, per_page=10)
    expenses = result['expenses']

    assert expenses[0]['date'] == '2024-01-05'
    assert expenses[1]['date'] == '2024-01-03'
    assert expenses[2]['date'] == '2024-01-01'

# ======================= CATEGORY TEST ==========================


def test_get_system_categories(test_db):
    """
    Test for fetching system categories
    """
    cateogry_list = get_system_categories()

    assert cateogry_list is not None


def test_get_user_category(insert_test_category):
    """
    Test for fetching user categories of a existing user
    """
    category_id_list, user_id = insert_test_category(["food", "groccery"])
    num_categories = len(category_id_list)
    category_list = get_user_categories(user_id)

    assert len(category_list) == num_categories

def test_get_user_category_not_found(test_db):
    """
    Test for fetching user categories of a non-existing user
    """

    category_list = get_user_categories(10)
    assert category_list == []

def test_create_user_category(test_db, insert_test_user):
    """
    Test for creating category for an existing user
    """
    cat_name = ['anime', 'netflix', 'gym']
    cat_id_list = []
    for cat in cat_name:
        cat_id = create_user_category(insert_test_user, cat.upper().replace(' ', '_'), cat)
        cat_id_list.append(cat_id)
    
    assert len(cat_id_list) == len(cat_name)
    
    for cat_id in cat_id_list:
        cat = test_db.execute(
            """SELECT * FROM user_categories WHERE user_id = ?
            AND id = ?
            """,
            (insert_test_user, cat_id)
        ).fetchone()

        assert cat["display_name"] in cat_name


def test_create_duplicate_user_category_returns_error(insert_test_category):
    """
    Test for creating a duplicate user category for an existing user
    """
    _, user_id = insert_test_category()
    cat = "test category"

    with pytest.raises(sqlite3.IntegrityError, match="User already has category"):
        create_user_category(user_id, cat.upper().replace(' ', '_'), cat)

def test_create_system_category_as_user_category_returns_error(test_db, insert_test_user):
    """
    Test for creating a system category as a user category
    """
    cat = "grocery"
    with pytest.raises(sqlite3.IntegrityError, match="already exists as a system category"):
        create_user_category(insert_test_user, cat.upper().replace(' ', '_'), cat)


def test_delete_user_category(test_db, insert_test_category):
    """
    Test deleting already existing user categories
    """
    category_id_list, user_id = insert_test_category()
    for cat_id in category_id_list:
        success = delete_user_category(cat_id, user_id)
        assert success
    
    for cat_id in category_id_list:
        category = test_db.execute(
            """SELECT * FROM user_categories WHERE id = ?
            AND user_id = ?
            """,
            (cat_id, user_id)
        ).fetchone()
        assert category is None

def test_delete_non_existing_user_category_returns_false(insert_test_user):
    """
    Test deleting non existent user category
    """
    success = delete_user_category(10, insert_test_user)
    assert not success


    

    


    
    
    



    
    




