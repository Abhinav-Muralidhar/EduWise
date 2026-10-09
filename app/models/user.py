from datetime import datetime, timezone
from app.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resources = db.relationship('Resource', backref='user', lazy=True)

    # Password reset
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Profile
    display_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.String(500), nullable=True)
    avatar_color = db.Column(db.String(7), default='#4361EE')

    # Session security
    session_version = db.Column(db.Integer, default=1, nullable=False)
