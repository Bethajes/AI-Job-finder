"""create applications table

Revision ID: e5f8b2a91c47
Revises: d8e1b4c7a905
Create Date: 2026-08-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f8b2a91c47'
down_revision: Union[str, None] = 'd8e1b4c7a905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False,
                  server_default='applied'),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('resume_url', sa.String(length=500), nullable=False),
        sa.Column('additional_documents', sa.JSON(), nullable=True),
        sa.Column('employer_notes', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=False,
                  server_default='web'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('interview_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status_change_count', sa.Integer(), nullable=False,
                  server_default='0'),
    )
    op.create_index(op.f('ix_applications_job_id'), 'applications', ['job_id'])
    op.create_index(op.f('ix_applications_applicant_id'), 'applications', ['applicant_id'])
    op.create_index(op.f('ix_applications_status'), 'applications', ['status'])
    op.create_index('ix_applications_job_id_status', 'applications',
                    ['job_id', 'status'])
    op.create_index('ix_applications_applicant_id_status', 'applications',
                    ['applicant_id', 'status'])
    op.create_index('ix_applications_applied_at', 'applications', ['applied_at'])


def downgrade() -> None:
    op.drop_index('ix_applications_applied_at', table_name='applications')
    op.drop_index('ix_applications_applicant_id_status', table_name='applications')
    op.drop_index('ix_applications_job_id_status', table_name='applications')
    op.drop_index(op.f('ix_applications_status'), table_name='applications')
    op.drop_index(op.f('ix_applications_applicant_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_job_id'), table_name='applications')
    op.drop_table('applications')
