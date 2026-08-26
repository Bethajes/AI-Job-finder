"""week 8: admin_logs, company verification, job moderation

Revision ID: b8e4c2a7d1f9
Revises: f7a1b3c5d7e9
Create Date: 2026-08-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b8e4c2a7d1f9'
down_revision: Union[str, None] = 'f7a1b3c5d7e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'admin_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_admin_logs_admin_id_created_at', 'admin_logs',
                    ['admin_id', 'created_at'])
    op.create_index('ix_admin_logs_action_type', 'admin_logs', ['action_type'])
    op.create_index('ix_admin_logs_resource', 'admin_logs',
                    ['resource_type', 'resource_id'])
    op.create_index('ix_admin_logs_created_at', 'admin_logs', ['created_at'])

    # Company verification lifecycle (Week 8). Existing verified companies
    # are grandfathered in as approved; everyone else starts pending.
    op.add_column('companies', sa.Column(
        'verification_status', sa.String(length=20), nullable=True,
        server_default='pending'))
    op.add_column('companies', sa.Column(
        'verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('companies', sa.Column(
        'admin_notes', sa.Text(), nullable=True))
    op.execute("UPDATE companies SET verification_status = "
               "CASE WHEN is_verified THEN 'approved' ELSE 'pending' END")

    # Job moderation columns (Week 8).
    op.add_column('jobs', sa.Column(
        'is_hidden', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('jobs', sa.Column(
        'is_flagged', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('jobs', sa.Column(
        'flagged_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('admin_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs', 'admin_notes')
    op.drop_column('jobs', 'flagged_at')
    op.drop_column('jobs', 'is_flagged')
    op.drop_column('jobs', 'is_hidden')
    op.drop_column('companies', 'admin_notes')
    op.drop_column('companies', 'verified_at')
    op.drop_column('companies', 'verification_status')
    op.drop_index('ix_admin_logs_created_at', table_name='admin_logs')
    op.drop_index('ix_admin_logs_resource', table_name='admin_logs')
    op.drop_index('ix_admin_logs_action_type', table_name='admin_logs')
    op.drop_index('ix_admin_logs_admin_id_created_at', table_name='admin_logs')
    op.drop_table('admin_logs')
