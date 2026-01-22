from flask import Blueprint, request, jsonify, session
import sqlite3
from database import get_system_categories, get_user_categories, create_user_category, delete_user_category
from utils import login_required
import heapq
import re

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
            system_categories = [cat['display_name'] for cat in get_system_categories()]
        except Exception as e:
            print(f"Get system category error: {e}")
            return jsonify({"error": "Internal server error"}), 500
        
        try:
            user_categories = [cat['display_name'] for cat in get_user_categories()]
        except Exception as e:
            print(f"Get user category error: {e}")
            return jsonify({"error": "Internal server error"}), 500
        
        categories = list(heapq.merge(system_categories, user_categories))
        
        return jsonify({
            "categories": categories,
            "summary": {
                "total": len(categories)
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
        
        display_name = data.get('display_name', '').strip()

        if len(display_name) > 100:
            return jsonify({"error": "Category name too long (max 100 characters)"}), 400
        
        if not re.match(r'^[a-zA-Z0-9 ]+$', display_name):
            return jsonify({
                "error": "Category name can only contain letters, numbers, and spaces"
            }), 400

        normalized_name = display_name.upper().replace(' ', '_')
        
        # create category in database
        category_id = create_user_category(
            user_id,
            normalized_name,
            display_name
        )


        return jsonify({
            "message": f"Category '{display_name}' created successfully",
            "category": {
                "id": category_id,
                "name": normalized_name,
                "display_name": display_name,
                "type": "user"
            }
        }), 201
    
    except sqlite3.IntegrityError as e:
        return jsonify({
            "error": f"Category '{display_name}' already exists"
        }), 409
    except Exception as e:
            print(f"Create category error: {e}")
            return jsonify({"error": "Constraint violation"}), 400
    
    
@categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
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
    

