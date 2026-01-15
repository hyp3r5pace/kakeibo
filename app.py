import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session
import bcrypt
from database import create_user, get_user_by_email, get_user_by_id
from auth import auth_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-very-secret-key-change-this-in-production'
app.secret_key = os.environ.get('SECRET_KEY')

if not app.secret_key:
    raise ValueError("No SECRET_KEY set! Create .env file with SECRET_KEY=...")

app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return "Expense Tracker API"

if __name__ == "__main__":
    app.run(debug=True)
