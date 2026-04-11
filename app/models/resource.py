from datetime import datetime
from app.extensions import db

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    resource_type = db.Column(db.String(50))
    topic = db.Column(db.String(250))
    filename = db.Column(db.String(250), nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
