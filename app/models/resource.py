from datetime import datetime, timezone
from app.extensions import db

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) 
    resource_type = db.Column(db.String(50))
    topic = db.Column(db.String(250))
    file_url = db.Column(db.String(250), nullable=True) 
    content_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
