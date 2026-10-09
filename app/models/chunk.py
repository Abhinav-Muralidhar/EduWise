import json
from datetime import datetime, timezone
from sqlalchemy.types import TypeDecorator, Text
from app.extensions import db

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

class FlexibleVector(TypeDecorator):
    """
    SQLAlchemy type decorator that uses pgvector's Vector(768) on PostgreSQL,
    and falls back to JSON-serialized Text on SQLite or environments without pgvector.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim=768, *args, **kwargs):
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql' and HAS_PGVECTOR:
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql' and HAS_PGVECTOR:
            return value
        if isinstance(value, (list, tuple)):
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql' and HAS_PGVECTOR:
            if hasattr(value, 'tolist'):
                return value.tolist()
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class KnowledgeChunk(db.Model):
    __tablename__ = 'knowledge_chunk'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('knowledge_source.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer, default=0, nullable=False)
    embedding = db.Column(FlexibleVector(768), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'content': self.content,
            'chunk_index': self.chunk_index
        }
