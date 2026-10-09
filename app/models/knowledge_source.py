from datetime import datetime, timezone
from app.extensions import db

class KnowledgeSource(db.Model):
    __tablename__ = 'knowledge_source'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(20), default='txt')  # 'pdf', 'docx', 'txt'
    file_url = db.Column(db.String(500), nullable=True)     # Cloudinary / storage URL if saved
    chunk_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    chunks = db.relationship('KnowledgeChunk', backref='source', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'source_type': self.source_type,
            'file_url': self.file_url,
            'chunk_count': self.chunk_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }
