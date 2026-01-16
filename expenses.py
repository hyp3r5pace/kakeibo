from flask import Blueprint, request, jsonify, session
from functools import wraps
from database import (
    create_expense,
    get_user_expenses,
    get_expense_by_id,
    update_expense,
    delete_expense
)
import re

expenses_bp = Blueprint('expenses', __name__)

def login_required(f):
    """
    Decorator to require login for a route
    
    Usage:
        @expenses_bp.route('/expenses', methods=['POST'])
        @login_required
        def create_expense():
            user_id = session['user_id']  # Guaranteed to exist
            # ... your code
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


@expenses_bp.route('/expenses', methods=['POST'])
@login_required
def create_new_expense():
    """
    Create a new expense
    Expected JSON: {
        "amount": 50.00,
        "type": "expense",  // or "income"
        "system_category_id": 1,  // optional
        "user_category_id": null,  // optional
        "description": "Lunch at restaurant",  // optional
        "date": "2026-01-15"  // YYYY-MM-DD format
    }
    """
    user_id = session["user_id"]
    try:
        if not request.is_json:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.json

        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        amount = data.get("amount")
        expense_type = data.get("type")
        date = data.get('date')

        if not amount or not expense_type or not date:
            return jsonify({"error": "amount, type, and date are required"}), 400

        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({"error": "Amount must be greater than 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid amount format"}), 400
        
        # Validate type
        if expense_type not in ['expense', 'income']:
            return jsonify({"error": "Type must be 'expense' or 'income'"}), 400
        
        # Validate date format (basic check)
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400
        
        # Extract optional fields
        system_category_id = data.get('system_category_id')
        user_category_id = data.get('user_category_id')
        description = data.get('description', '').strip()

        # Validate category constraints (at most one category)
        if system_category_id and user_category_id:
            return jsonify({"error": "Cannot set both system and user category"}), 400
        
        # Create expense in database
        expense_id = create_expense(
            user_id=user_id,
            amount=amount,
            expense_type=expense_type,
            system_category_id=system_category_id,
            user_category_id=user_category_id,
            description=description if description else None,
            date=date
        )
        if not expense_id:
            return jsonify({"error": "Failed to create expense"}), 500
        
        # Fetch the created expense to return complete info
        expense = get_expense_by_id(expense_id, user_id)

        return jsonify({
            "message": "Expense created successfully",
            "expense": expense
        }), 201
    except Exception as e:
        print(f"Create expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@expenses_bp.route('/expenses', methods=['GET'])
@login_required
def list_expenses():
    """
    Get all expenses for logged-in user with optional filters
    Query parameters:
        - start_date: Filter by start date (YYYY-MM-DD)
        - end_date: Filter by end date (YYYY-MM-DD)
        - category_id: Filter by category ID
        - type: Filter by type ('expense' or 'income')
    
    Example: GET /expenses?start_date=2026-01-01&end_date=2026-01-31&type=expense
    """
    user_id = session['user_id']
    try:
        # Get query parameters (filters)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        system_category_id = request.args.get('system_category_id')
        user_category_id = request.args.get('user_category_id')
        expense_type = request.args.get('type')

        # Validate type if provided
        if expense_type and expense_type not in ['expense', 'income']:
            return jsonify({"error": "Type must be 'expense' or 'income'"}), 400

        
        # Convert category_id to int if provided
        if system_category_id:
            try:
                system_category_id = int(system_category_id)
            except ValueError:
                return jsonify({"error": "Invalid system_category_id"}), 400
        
        if user_category_id:
            try:
                user_category_id = int(user_category_id)
            except ValueError:
                return jsonify({"error": "Invalid user_category_id"}), 400
            
        # Get expenses
        expenses = get_user_expenses(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            system_category_id=system_category_id,
            user_category_id=user_category_id,
            expense_type=expense_type
        )

        return jsonify({
            "expenses": expenses
        }), 200
    
    except Exception as e:
        print(f"List expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@expenses_bp.route('/expenses/<int:expense_id>')    
@login_required
def get_expense(expense_id):
    """
    Get a specific expense by ID
    """
    user_id = session['user_id']
    try:
        expense = get_expense_by_id(expense_id, user_id) # sending both user_id and expense_id, prevents IDOR
        if not expense:
            return jsonify({"error": "Expense not found"}), 404
        return jsonify({"expense": expense}), 200
    except Exception as e:
        print(f"get expense by ID error: {e}")
        return jsonify({"error": "Interal server error"}), 500
    

@expenses_bp.route('/expenses/<int:expense_id>/', methods=['PUT'])
@login_required
def update_expense_route(expense_id):
    """
    Update an expense
    Expected JSON (all fields optional): {
        "amount": 55.00,
        "type": "expense",
        "system_category_id": 2,
        "user_category_id": null,
        "description": "Updated description",
        "date": "2026-01-16"
    }    
    """
    user_id = session['user_id']
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.json

        if data is None:
            return jsonify({"error": "Invalid JSON!"}), 400
        
        # Extract fields
        amount = data.get('amount')
        expense_type = data.get('type')
        system_category_id = data.get('system_category_id')
        user_category_id = data.get('user_category_id')
        description = data.get('description')
        date = data.get('date')

        if amount is not None:
            try:
                amount = float(amount)
                if amount <= 0:
                    return jsonify({"error": "Amount must be greater than 0"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid amount format"}), 400

        # Validate type if provided
        if expense_type and expense_type not in ['expense', 'income']:
            return jsonify({"error": "Type must be 'expense' or 'income'"}), 400
        
        # Validate date format if provided
        if date:
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400

        # Validate category constraint
        if system_category_id and user_category_id:
            return jsonify({"error": "Cannot set both system and user category"}), 400

        # Update expense
        success = update_expense(
            expense_id=expense_id,
            user_id=user_id,
            amount=amount,
            expense_type=expense_type,
            system_category_id=system_category_id,
            user_category_id=user_category_id,
            description=description,
            date=date
        )
        
        if not success:
            return jsonify({"error": "Expense not found or update failed"}), 404

        # Fetch updated expense
        expense = get_expense_by_id(expense_id, user_id)

        return jsonify({
            "message": "Expense updated successfully",
            "expense": expense
        }), 200        
    except Exception as e:
        print(f"update expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@expenses_bp.route('/expense/<int:expense_id>', methods=['DELETE'])    
@login_required
def delete_expense_route(expense_id):
    """
    Delete an expense    
    """
    user_id = session["user_id"]
    try:
        success = delete_expense(expense_id, user_id)
        if not success:
            return jsonify({"error": "Expense not found"}), 404
        
        return jsonify({"message": "Expense deleted successfully"}), 200
    except Exception as e:
        print(f"Delete expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    
    
              
