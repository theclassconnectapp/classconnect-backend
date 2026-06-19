"""college schema

Revision ID: 0002_college_schema
Revises: 0001_initial_users
Create Date: 2026-06-20 00:00:03.114191
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0002_college_schema'
down_revision: Union[str, None] = '0001_initial_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('colleges',
    sa.Column('id', sa.String(length=128), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=True),
    sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_colleges_active', 'colleges', ['active'], unique=False)
    op.create_table('departments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('college_id', sa.String(length=128), nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.String(length=128), nullable=True),
    sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('college_id', 'slug', name='uq_departments_college_slug')
    )
    op.create_index('ix_departments_college_id', 'departments', ['college_id'], unique=False)
    op.create_table('batches',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('department_id', sa.Uuid(), nullable=False),
    sa.Column('label', sa.String(length=32), nullable=False),
    sa.Column('start_year', sa.Integer(), nullable=False),
    sa.Column('end_year', sa.Integer(), nullable=False),
    sa.Column('archived', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_year = start_year + 4', name='ck_batches_four_year_window'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('department_id', 'start_year', 'end_year', name='uq_batches_department_years')
    )
    op.create_index('ix_batches_department_id', 'batches', ['department_id'], unique=False)
    op.create_table('user_scopes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('uid', sa.String(length=128), nullable=False),
    sa.Column('college_id', sa.String(length=128), nullable=False),
    sa.Column('department_id', sa.Uuid(), nullable=False),
    sa.Column('batch_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['uid'], ['users.uid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_scopes_batch_id', 'user_scopes', ['batch_id'], unique=False)
    op.create_index('ix_user_scopes_department_id', 'user_scopes', ['department_id'], unique=False)
    op.create_index('ix_user_scopes_uid', 'user_scopes', ['uid'], unique=False)
    op.add_column('users', sa.Column('department_id', sa.Uuid(), nullable=True))
    op.add_column('users', sa.Column('batch_id', sa.Uuid(), nullable=True))
    op.create_index('ix_users_batch_id', 'users', ['batch_id'], unique=False)
    op.create_index('ix_users_department_id', 'users', ['department_id'], unique=False)
    op.create_foreign_key('fk_users_batch_id_batches', 'users', 'batches', ['batch_id'], ['id'])
    op.create_foreign_key('fk_users_department_id_departments', 'users', 'departments', ['department_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_users_department_id_departments', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_batch_id_batches', 'users', type_='foreignkey')
    op.drop_index('ix_users_department_id', table_name='users')
    op.drop_index('ix_users_batch_id', table_name='users')
    op.drop_column('users', 'batch_id')
    op.drop_column('users', 'department_id')
    op.drop_index('ix_user_scopes_uid', table_name='user_scopes')
    op.drop_index('ix_user_scopes_department_id', table_name='user_scopes')
    op.drop_index('ix_user_scopes_batch_id', table_name='user_scopes')
    op.drop_table('user_scopes')
    op.drop_index('ix_batches_department_id', table_name='batches')
    op.drop_table('batches')
    op.drop_index('ix_departments_college_id', table_name='departments')
    op.drop_table('departments')
    op.drop_index('ix_colleges_active', table_name='colleges')
    op.drop_table('colleges')
