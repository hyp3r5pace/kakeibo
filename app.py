import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session
import bcrypt
from database import create_user, get_user_by_email, get_user_by_id
from auth import auth_bp
from expenses import expenses_bp
from categories import categories_bp
from datetime import timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

if not app.secret_key:
    raise ValueError("No SECRET_KEY set! Create .env file with SECRET_KEY=...")

# Environment
ENV = os.environ.get('FLASK_ENV', 'development')

# Session security configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Secure flag only in production (requires HTTPS)
if ENV == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True

app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(categories_bp)

@app.route('/')
def home():
    return "Expense Tracker API"

if __name__ == "__main__":
    app.run(debug=True)
