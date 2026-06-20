"""ai usage

Revision ID: 0003_ai_usage
Revises: 0002_college_schema
Create Date: 2026-06-20 00:00:03.114191
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003_ai_usage'
down_revision: Union[str, None] = '0002_college_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_usage',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('uid', sa.String(length=128), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ai_usage_uid', 'ai_usage', ['uid'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_ai_usage_uid', table_name='ai_usage')
    op.drop_table('ai_usage')
