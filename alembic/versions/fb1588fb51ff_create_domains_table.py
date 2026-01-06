"""create domains table

Revision ID: fb1588fb51ff
Revises: 
Create Date: 2025-11-24 03:00:33.063844

"""
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fb1588fb51ff'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "domains",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("protocol", sa.String(10), nullable=False),
        sa.Column("crawl_delay", sa.SmallInteger, default=5),
        sa.Column("has_robots_txt", sa.Boolean, default=None),
        sa.Column("is_blocked", sa.Boolean, default=None),
        sa.Column("last_crawled_at", sa.DateTime, default=None),
        sa.Column("last_processed_at", sa.DateTime, default=None),
        sa.Column("first_discovered_at", sa.DateTime, default=datetime.now()),
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("domains")
    pass
