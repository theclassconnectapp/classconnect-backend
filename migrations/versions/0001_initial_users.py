"""initial users table

Revision ID: 0001_initial_users
Revises:
Create Date: 2026-06-20 00:00:03.114191
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0001_initial_users'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('uid', sa.String(length=128), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=False),
    sa.Column('dept', sa.String(length=128), nullable=True),
    sa.Column('batch', sa.String(length=32), nullable=True),
    sa.Column('photo_url', sa.String(length=1024), nullable=True),
    sa.Column('fcm_token', sa.String(length=512), nullable=True),
    sa.Column('college_id', sa.String(length=128), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('uid'),
    sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_college_id', 'users', ['college_id'], unique=False)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_college_id', table_name='users')
    op.drop_table('users')
