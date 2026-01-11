"""create links table

Revision ID: 8dd0ff5fc030
Revises: fb1588fb51ff
Create Date: 2025-11-24 03:05:28.739503

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from src.models.Link import ChangeFreq

# revision identifiers, used by Alembic.
revision: str = "8dd0ff5fc030"
down_revision: Union[str, Sequence[str], None] = "fb1588fb51ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

enum_type = sa.Enum(ChangeFreq, name="changefreq_enum")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "links",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("url", sa.String(512), unique=True, nullable=False),
        sa.Column("change_freq", enum_type, default=ChangeFreq.MONTHLY),
        sa.Column("priority", sa.Float(1), default=0.5),
        sa.Column("lang", sa.String(3), default=None),
        sa.Column("content", sa.Text, default=None),
        sa.Column("title", sa.String(100), default=None),
        sa.Column("description", sa.String(250), default=None),
        sa.Column("http_status", sa.SmallInteger, default=None),
        sa.Column("content_type", sa.String(30), default=None),
        sa.Column("keywords", sa.String(100), default=None),
        sa.Column("last_crawled_at", sa.DateTime, default=None),
        sa.Column("first_discovered_at", sa.DateTime, default=datetime.now()),
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("links")
    enum_type.drop(op.get_bind(), checkfirst=False)
    pass
