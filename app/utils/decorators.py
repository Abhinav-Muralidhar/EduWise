from functools import wraps
from flask import session, flash, redirect, url_for
from app.models.user import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
        
        user = User.query.get(user_id)
        session_version = session.get('session_version')
        if not user or session_version != user.session_version:
            session.clear()
            flash("Your session has expired or is invalid. Please log in again.", "warning")
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function
