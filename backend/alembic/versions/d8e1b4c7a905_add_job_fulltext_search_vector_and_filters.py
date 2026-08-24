"""add job full-text search vector and filter indexes

Revision ID: d8e1b4c7a905
Revises: c3d94a7f21b8
Create Date: 2026-08-24 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd8e1b4c7a905'
down_revision: Union[str, None] = 'c3d94a7f21b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Weights: title='A', description='B', requirements='B', location='C'.
# The two-argument to_tsvector('english', ...) is IMMUTABLE, which is
# required for a STORED generated column.
SEARCH_VECTOR_SQL = """
setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
setweight(to_tsvector('english', coalesce(requirements::text, '')), 'B') ||
setweight(to_tsvector('english', coalesce(location, '')), 'C')
"""


def upgrade() -> None:
    # 1) Generated tsvector column (PostgreSQL keeps it in sync automatically)
    op.execute(
        f"ALTER TABLE jobs ADD COLUMN search_vector tsvector "
        f"GENERATED ALWAYS AS ({SEARCH_VECTOR_SQL}) STORED"
    )

    # 2) GIN index so search_vector @@ query uses index scans
    op.create_index(
        'ix_jobs_search_vector',
        'jobs',
        ['search_vector'],
        postgresql_using='gin',
    )

    # 3) Indexes for frequently filtered columns
    op.create_index('ix_jobs_employment_type', 'jobs', ['employment_type'])
    op.create_index('ix_jobs_experience_level', 'jobs', ['experience_level'])
    op.create_index(
        'ix_jobs_is_remote_status_posted_date',
        'jobs',
        ['is_remote', 'status', 'posted_date'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_jobs_is_remote_status_posted_date', table_name='jobs'
    )
    op.drop_index('ix_jobs_experience_level', table_name='jobs')
    op.drop_index('ix_jobs_employment_type', table_name='jobs')
    op.drop_index('ix_jobs_search_vector', table_name='jobs')
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS search_vector")
