"""add knowledge_source and chunk tables with vector support

Revision ID: e5a7b8c9d0e1
Revises: 0183ba6ffecc
Create Date: 2026-10-05 00:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

# revision identifiers, used by Alembic.
revision = 'e5a7b8c9d0e1'
down_revision = '0183ba6ffecc'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Create knowledge_source table
    op.create_table(
        'knowledge_source',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=20), server_default='txt', nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('chunk_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    # Embedding column type
    if is_postgres and HAS_PGVECTOR:
        embedding_col = sa.Column('embedding', Vector(768), nullable=True)
    else:
        embedding_col = sa.Column('embedding', sa.Text(), nullable=True)

    # Create knowledge_chunk table
    op.create_table(
        'knowledge_chunk',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('knowledge_source.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), server_default='0', nullable=False),
        embedding_col,
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )


def downgrade():
    op.drop_table('knowledge_chunk')
    op.drop_table('knowledge_source')
