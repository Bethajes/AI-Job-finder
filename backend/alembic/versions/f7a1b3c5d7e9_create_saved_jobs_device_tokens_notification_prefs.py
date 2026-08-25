"""create saved_jobs, device_tokens tables and add notification_preferences to users

Revision ID: f7a1b3c5d7e9
Revises: e5f8b2a91c47
Create Date: 2026-08-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f7a1b3c5d7e9'
down_revision: Union[str, None] = 'e5f8b2a91c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── saved_jobs ─────────────────────────────────────────────────────
    op.create_table(
        'saved_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_id', 'job_id', name='uq_saved_jobs_user_job'),
    )
    op.create_index('ix_saved_jobs_user_active_created', 'saved_jobs',
                    ['user_id', 'is_active', 'created_at'])
    op.create_index(op.f('ix_saved_jobs_job_id'), 'saved_jobs', ['job_id'])

    # ── device_tokens ──────────────────────────────────────────────────
    op.create_table(
        'device_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('device_type', sa.String(length=10), nullable=False,
                  server_default='android'),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('token_hash', name='uq_device_tokens_token_hash'),
    )
    op.create_index(op.f('ix_device_tokens_token_hash'), 'device_tokens', ['token_hash'], unique=True)
    op.create_index('ix_device_tokens_user_id_active', 'device_tokens',
                    ['user_id', 'is_active'])

    # ── users: add notification_preferences JSONB column ───────────────
    op.add_column('users', sa.Column('notification_preferences', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'notification_preferences')
    op.drop_index('ix_device_tokens_user_id_active', table_name='device_tokens')
    op.drop_index(op.f('ix_device_tokens_token_hash'), table_name='device_tokens')
    op.drop_table('device_tokens')
    op.drop_index(op.f('ix_saved_jobs_job_id'), table_name='saved_jobs')
    op.drop_index('ix_saved_jobs_user_active_created', table_name='saved_jobs')
    op.drop_table('saved_jobs')
