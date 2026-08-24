"""create jobs table

Revision ID: c3d94a7f21b8
Revises: b602f97bfbbb
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d94a7f21b8'
down_revision: Union[str, None] = 'b602f97bfbbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.JSON(), nullable=True),
        sa.Column('responsibilities', sa.JSON(), nullable=True),
        sa.Column('employment_type', sa.String(length=20), nullable=False),
        sa.Column('experience_level', sa.String(length=20), nullable=False),
        sa.Column('salary_min', sa.Numeric(12, 2), nullable=True),
        sa.Column('salary_max', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('is_remote', sa.Boolean(), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('posted_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('application_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('posted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=False),
        sa.Column('applications_count', sa.Integer(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_jobs_company_id'), 'jobs', ['company_id'])
    op.create_index(op.f('ix_jobs_posted_by_id'), 'jobs', ['posted_by_id'])
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'])
    op.create_index(op.f('ix_jobs_posted_date'), 'jobs', ['posted_date'])
    op.create_index('ix_jobs_company_id_status', 'jobs', ['company_id', 'status'])
    op.create_index('ix_jobs_status_posted_date', 'jobs', ['status', 'posted_date'])
    op.create_index('ix_jobs_category', 'jobs', ['category'])


def downgrade() -> None:
    op.drop_index('ix_jobs_category', table_name='jobs')
    op.drop_index('ix_jobs_status_posted_date', table_name='jobs')
    op.drop_index('ix_jobs_company_id_status', table_name='jobs')
    op.drop_index(op.f('ix_jobs_posted_date'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_posted_by_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_company_id'), table_name='jobs')
    op.drop_table('jobs')
