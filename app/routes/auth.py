import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, limiter
from app.models.user import User
from app.models.resource import Resource
from app.services.email import send_reset_email
from app.utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)


# ---------------------------------------------------------------------------
# Signup (with password validation + confirm password)
# ---------------------------------------------------------------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def signup():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if not username or not email or not password:
            flash("Username, email, and password are required.", "danger")
            return redirect(url_for('auth.signup'))

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return redirect(url_for('auth.signup'))

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for('auth.signup'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.signup'))
        
        user_exists = User.query.filter(
            (db.func.lower(User.username) == username.lower()) | 
            (db.func.lower(User.email) == email)
        ).first()

        if user_exists:
            flash("Username or Email already exists.", "danger")
            return redirect(url_for('auth.signup'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created! Please log in.", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html')


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login():
    if request.method == 'POST':
        identifier = (request.form.get('username_or_email') or '').strip()
        password = request.form.get('password') or ''
        remember = bool(request.form.get('remember_me'))

        if not identifier or not password:
            flash("Username/email and password are required.", "danger")
            return render_template('login.html')
        
        # Case-insensitive lookup for both username and email
        user = User.query.filter(
            (db.func.lower(User.username) == identifier.lower()) | 
            (db.func.lower(User.email) == identifier.lower())
        ).first()

        if user and check_password_hash(user.password, password):
            session.permanent = remember
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard.index'))
        else:
            flash("Invalid username/email or password.", "danger")
    
    return render_template('login.html')


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        user = User.query.filter(db.func.lower(User.email) == email).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()

            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_reset_email(user.email, reset_url)

        # Always show the same message — don't leak whether the email exists
        flash("If an account exists with that email, we've sent a reset link.", "info")
        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')


# ---------------------------------------------------------------------------
# Reset Password (from email link)
# ---------------------------------------------------------------------------
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.now(timezone.utc):
        flash("This reset link is invalid or has expired.", "danger")
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template('reset_password.html', token=token)
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', token=token)

        user.password = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)


# ---------------------------------------------------------------------------
# User Profile
# ---------------------------------------------------------------------------
@auth_bp.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    stats = {
        'total': Resource.query.filter_by(user_id=user.id).count(),
        'pptx': Resource.query.filter_by(user_id=user.id, resource_type='pptx').count(),
        'pdf': Resource.query.filter_by(user_id=user.id, resource_type='pdf').count(),
        'quiz': Resource.query.filter_by(user_id=user.id, resource_type='quiz').count(),
        'flashcard': Resource.query.filter_by(user_id=user.id, resource_type='flashcard').count(),
        'explanation': Resource.query.filter_by(user_id=user.id, resource_type='explanation').count(),
        'summary': Resource.query.filter_by(user_id=user.id, resource_type='summary').count(),
        'favorites': Resource.query.filter_by(user_id=user.id, is_favorite=True).count(),
    }
    return render_template('profile.html', user=user, stats=stats)


# ---------------------------------------------------------------------------
# Update Profile (display name, bio)
# ---------------------------------------------------------------------------
@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    display_name = (request.form.get('display_name') or '').strip()[:100]
    bio = (request.form.get('bio') or '').strip()[:500]

    user.display_name = display_name or None
    user.bio = bio or None
    db.session.commit()

    # Keep session username in sync if they update display name
    flash("Profile updated!", "success")
    return redirect(url_for('auth.profile'))


# ---------------------------------------------------------------------------
# Change Password (from profile page)
# ---------------------------------------------------------------------------
@auth_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not check_password_hash(user.password, current_pw):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for('auth.profile'))
    if len(new_pw) < 8:
        flash("New password must be at least 8 characters.", "danger")
        return redirect(url_for('auth.profile'))
    if new_pw != confirm_pw:
        flash("New passwords do not match.", "danger")
        return redirect(url_for('auth.profile'))

    user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash("Password updated successfully!", "success")
    return redirect(url_for('auth.profile'))


# ---------------------------------------------------------------------------
# Delete Account
# ---------------------------------------------------------------------------
@auth_bp.route('/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    password = request.form.get('password', '')
    if not check_password_hash(user.password, password):
        flash("Incorrect password. Account not deleted.", "danger")
        return redirect(url_for('auth.profile'))

    # Delete all user resources first
    Resource.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    session.clear()

    flash("Your account and all data have been permanently deleted.", "info")
    return redirect(url_for('auth.login'))
