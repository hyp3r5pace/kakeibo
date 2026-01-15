import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session
import bcrypt
from database import create_user, get_user_by_email

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-very-secret-key-change-this-in-production'
app.secret_key = os.environ.get('SECRET_KEY')

if not app.secret_key:
    raise ValueError("No SECRET_KEY set! Create .env file with SECRET_KEY=...")

@app.route('/')
def home():
    return "Expense Tracker API"

@app.route('/register', methods=['POST'])
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
    


if __name__ == "__main__":
    app.run(debug=True)
