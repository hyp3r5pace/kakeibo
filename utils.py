# utils.py
from functools import wraps
from flask import session, jsonify

def login_required(f):
    """
    Decorator to require login for a route
    
    Usage:
        @expenses_bp.route('/expenses', methods=['POST'])
        @login_required
        def create_expense():
            user_id = session['user_id']  # Guaranteed to exist
            # ... your code
    
    If user is not logged in, returns 401 Unauthorized.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function