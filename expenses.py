# expenses.py
from flask import Blueprint, request, jsonify, session
import sqlite3
import re
from utils import login_required
from database import (
    create_expense,
    get_user_expenses,
    get_expense_by_id,
    update_expense,
    delete_expense
)

expenses_bp = Blueprint('expenses', __name__)


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
    user_id = session['user_id']
    
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.json
        
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract and validate required fields
        amount = data.get('amount')
        expense_type = data.get('type')
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
        
        # Fetch the created expense to return complete info
        expense = get_expense_by_id(expense_id, user_id)
        
        return jsonify({
            "message": "Expense created successfully",
            "expense": expense
        }), 201
        
    except sqlite3.IntegrityError as e:
        # Handle constraint violations
        error_str = str(e).lower()
        
        if "check constraint" in error_str:
            if "amount" in error_str:
                return jsonify({"error": "Amount must be greater than 0"}), 400
            elif "type" in error_str:
                return jsonify({"error": "Type must be 'expense' or 'income'"}), 400
            else:
                return jsonify({"error": "Invalid expense data"}), 400
        
        elif "foreign key constraint" in error_str:
            return jsonify({"error": "Invalid category ID"}), 400
        
        else:
            print(f"Create expense integrity error: {e}")
            return jsonify({"error": "Constraint violation"}), 400
    
    except Exception as e:
        print(f"Create expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@expenses_bp.route('/expenses', methods=['GET'])
@login_required
def list_expenses():
    """
    Get all expenses for logged-in user with optional filters
    Query parameters:
        - page: Page number (default: 1, min: 1)
        - per_page: Items per page (default: 20, min: 1, max: 100)
        - start_date: Filter by start date (YYYY-MM-DD)
        - end_date: Filter by end date (YYYY-MM-DD)
        - system_category_id: Filter by system category ID
        - user_category_id: Filter by user category ID
        - type: Filter by type ('expense' or 'income')

    Example: GET /expenses?page=2&per_page=50&start_date=2026-01-01&end_date=2026-01-31&type=expense
    """
    user_id = session['user_id']
    
    try:
        # Extract and validate pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # validate and clamp
        page = max(1, page)
        per_page = max(1, min(100, per_page))

        # Get query parameters (filters)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        system_category_id = request.args.get('system_category_id')
        user_category_id = request.args.get('user_category_id')
        expense_type = request.args.get('type')
        
        # Validate type if provided
        if expense_type and expense_type not in ['expense', 'income']:
            return jsonify({"error": "Type must be 'expense' or 'income'"}), 400
        
        # Convert category IDs to int if provided
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
        
        # Get expenses from database
        result = get_user_expenses(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            system_category_id=system_category_id,
            user_category_id=user_category_id,
            expense_type=expense_type,
            page=page,
            per_page=per_page
        )

        expenses = result['expenses']
        total_count = result['total_count']

        total_pages = (total_count + per_page - 1) // per_page

        has_previous = page > 1
        has_next = page < total_pages
        
        # Calculate summary statistics
        total_expenses = sum(e['amount'] for e in expenses if e['type'] == 'expense')
        total_income = sum(e['amount'] for e in expenses if e['type'] == 'income')
        net = total_income - total_expenses
        
        return jsonify({
            "expenses": expenses,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_previous": has_previous,
                "has_next": has_next 
            },
            "summary": {
                "count": len(expenses),
                "total_expenses": total_expenses,
                "total_income": total_income,
                "net": net
            }
        }), 200
        
    except Exception as e:
        print(f"List expenses error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@expenses_bp.route('/expenses/<int:expense_id>', methods=['GET'])
@login_required
def get_expense(expense_id):
    """Get a specific expense by ID"""
    user_id = session['user_id']
    
    try:
        expense = get_expense_by_id(expense_id, user_id)
        
        if not expense:
            return jsonify({"error": "Expense not found"}), 404
        
        return jsonify({"expense": expense}), 200
        
    except Exception as e:
        print(f"Get expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@expenses_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
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
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract fields (all optional for update)
        amount = data.get('amount')
        expense_type = data.get('type')
        system_category_id = data.get('system_category_id')
        user_category_id = data.get('user_category_id')
        description = data.get('description')
        date = data.get('date')
        
        # Validate amount if provided
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
        
    except sqlite3.IntegrityError as e:
        # Handle constraint violations
        error_str = str(e).lower()
        
        if "check constraint" in error_str:
            if "amount" in error_str:
                return jsonify({"error": "Amount must be greater than 0"}), 400
            elif "type" in error_str:
                return jsonify({"error": "Type must be 'expense' or 'income'"}), 400
            else:
                return jsonify({"error": "Invalid expense data"}), 400
        
        elif "foreign key constraint" in error_str:
            return jsonify({"error": "Invalid category ID"}), 400
        
        else:
            print(f"Update expense integrity error: {e}")
            return jsonify({"error": "Constraint violation"}), 400
    
    except Exception as e:
        print(f"Update expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@expenses_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense_route(expense_id):
    """Delete an expense"""
    user_id = session['user_id']
    
    try:
        success = delete_expense(expense_id, user_id)
        
        if not success:
            return jsonify({"error": "Expense not found"}), 404
        
        return jsonify({"message": "Expense deleted successfully"}), 200
        
    except Exception as e:
        print(f"Delete expense error: {e}")
        return jsonify({"error": "Internal server error"}), 500