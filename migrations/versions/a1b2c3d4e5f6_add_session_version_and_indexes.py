"""add session_version and indexes on foreign keys

Revision ID: a1b2c3d4e5f6
Revises: e5a7b8c9d0e1
Create Date: 2026-10-09 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'e5a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    # Add session_version to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session_version', sa.Integer(), server_default='1', nullable=False))

    # Add index on resource(user_id)
    with op.batch_alter_table('resource', schema=None) as batch_op:
        batch_op.create_index('ix_resource_user_id', ['user_id'], unique=False)

    # Add index on knowledge_source(user_id)
    with op.batch_alter_table('knowledge_source', schema=None) as batch_op:
        batch_op.create_index('ix_knowledge_source_user_id', ['user_id'], unique=False)

    # Add index on knowledge_chunk(source_id)
    with op.batch_alter_table('knowledge_chunk', schema=None) as batch_op:
        batch_op.create_index('ix_knowledge_chunk_source_id', ['source_id'], unique=False)


def downgrade():
    # Drop index on knowledge_chunk(source_id)
    with op.batch_alter_table('knowledge_chunk', schema=None) as batch_op:
        batch_op.drop_index('ix_knowledge_chunk_source_id')

    # Drop index on knowledge_source(user_id)
    with op.batch_alter_table('knowledge_source', schema=None) as batch_op:
        batch_op.drop_index('ix_knowledge_source_user_id')

    # Drop index on resource(user_id)
    with op.batch_alter_table('resource', schema=None) as batch_op:
        batch_op.drop_index('ix_resource_user_id')

    # Drop session_version from user
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('session_version')
