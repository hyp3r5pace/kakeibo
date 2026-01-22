from flask import Blueprint, request, jsonify, session
import sqlite3
from database import get_system_categories, get_user_categories, create_custom_user_category, delete_user_category
from utils import login_required
import heapq

# Create blueprint
categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """
    GET system and user categories of user_id
    """
    user_id = session["user_id"]
    
    try:
        try:
            system_categories = [cat.display_name for cat in get_system_categories(user_id)]
        except Exception as e:
            print(f"Get system category error: {e}")
            return jsonify({"error": "Internal server error"}), 500
        
        try:
            user_categories = [cat.display_name for cat in get_user_categories(user_id)]
        except Exception as e:
            print(f"Get user category error: {e}")
            return jsonify({"error": "Internal server error"}), 500
        
        categories = list(heapq.merge(system_categories, user_categories))
        
        return jsonify({
            "categories": categories,
            "summary": {
                "count": len(categories)
            } 
        }), 200
    except Exception as e:
        print(f"Get categories error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
    
@categories_bp.route('/categories', methods=['POST'])
@login_required
def post_category():
    """
    Create new category
    Expected JSON: {
        "display_name": "food"
    }
    """
    user_id = session['user_id']
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.json

        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        display_name = data.get('display_name').strip()

        if not display_name:
            return jsonify({"error": "display name cannot be empty"}), 400
        
        # create category in database
        category_id = create_custom_user_category(
            user_id,
            display_name.upper(),
            display_name
        )

        if not category_id:
            return jsonify({"error": f"{display_name} exist as system category or it already exist as user category"}), 409
        
        return jsonify({"message": f"category {display_name} created successfully"}), 200
    except sqlite3.IntegrityError as e:
        err_str = str(e).lower()

        if "foreign key constraint" in err_str:
            return jsonify({"error": "Invalid user ID"}), 400
        else:
            print(f"Create expense integrity error: {e}")
            return jsonify({"error": "Constraint violation"}), 400
    except Exception as e:
            print(f"Create expense integrity error: {e}")
            return jsonify({"error": "Constraint violation"}), 400
    
    
@categories_bp.route('/categories/<int:category_id>', methods=['POST'])
@login_required
def delete_user_category_route(category_id):
    """
    Delete a category
    """
    user_id = session['user_id']
    try:
        success = delete_user_category(category_id, user_id)

        if not success:
            return jsonify({"error: category not found"}), 404
        
        return jsonify({"message": "Category deleted successfully"}), 200
    except Exception as e:
        print(f"Delete category error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    

