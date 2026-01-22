# auth.py
from flask import Blueprint, request, jsonify, session
import bcrypt
import re
import sqlite3
from database import create_user, get_user_by_email, get_user_by_id

# Create a Blueprint
auth_bp = Blueprint('auth', __name__)


def is_valid_email(email):
    """Basic email format validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Expected JSON: {
        "email": "user@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.json
        
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Validate required fields
        if not email or not password or not first_name or not last_name:
            return jsonify({"error": "All fields are required"}), 400
        
        # Validate email format
        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Validate password length
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        
        # Validate name lengths
        if len(first_name) > 50 or len(last_name) > 50:
            return jsonify({"error": "Names must be 50 characters or less"}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user in database
        user_id = create_user(email, password_hash, first_name, last_name)
        
        # Log the user in automatically
        session['user_id'] = user_id
        
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
        }), 201
        
    except sqlite3.IntegrityError as e:
        # Email already exists (UNIQUE constraint violation)
        error_str = str(e).lower()
        if "unique constraint" in error_str or "email" in error_str:
            return jsonify({"error": "Email already registered"}), 409
        else:
            # Other integrity error
            print(f"Registration integrity error: {e}")
            return jsonify({"error": "Registration failed"}), 400
    
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    Expected JSON: {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.json
        
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Get user from database
        user = get_user_by_email(email)
        
        if not user:
            # Generic error message (don't reveal if email exists)
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Verify password
        password_matches = bcrypt.checkpw(
            password.encode('utf-8'),
            user['password_hash']
        )
        
        if not password_matches:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Create session
        session['user_id'] = user['id']
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "first_name": user['first_name'],
                "last_name": user['last_name']
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# should I check if user is logged in or not
# if not logged in, send msg, "you are not logged in"
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        session.clear()
        return jsonify({"message": "Logout successful"}), 200
        
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get currently logged-in user's info"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Not logged in"}), 401
        
        user_id = session['user_id']
        
        # Get user from database
        user = get_user_by_id(user_id)
        
        if not user:
            # Session has invalid user_id (user was deleted)
            session.clear()
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user": {
                "id": user['id'],
                "email": user['email'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "created_at": user['created_at']
            }
        }), 200
        
    except Exception as e:
        print(f"Get current user error: {e}")
        return jsonify({"error": "Internal server error"}), 500