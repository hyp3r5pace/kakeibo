from flask import Blueprint, request, jsonify, session
import bcrypt
import re
from database import create_user, get_user_by_email, get_user_by_id

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Expected JSON: {
        "email": "user@example.com",
        "password": "secretpassword",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content type must be application/json"}), 400
        
        data = request.json
        # extract and validate data
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        # validation
        if not email or not password or not first_name or not last_name:
            return jsonify({"error": "All fields required"}), 400
        
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        
        # check if user already exist
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({"error": "Email already registered"}), 409
        
        # hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_id = create_user(email, password_hash, first_name, last_name)

        if not user_id:
            return jsonify({"error": "Failed to create user"}), 500
        
        session['user_id'] = user_id

        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
        }), 201
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500


    
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    Expected JSON: {
        "email": "user@example.com",
        "password": "secretpassword"
    }
    """
    try:
        # Check if JSON was sent
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.json
        
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract input
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        # Find user by email
        user = get_user_by_email(email)
        
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Verify password
        stored_hash = user['password_hash']
        
        # bcrypt.checkpw expects bytes
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Create session (log user in)
        session['user_id'] = user['id']
        
        # Return user info
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
    

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user by clearing session
    """
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Clear the user_id from session
    session.pop('user_id', None)
    
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get currently logged-in user's info
    """
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user": {
            "id": user['id'],
            "email": user['email'],
            "first_name": user['first_name'],
            "last_name": user['last_name']
        }
    }), 200