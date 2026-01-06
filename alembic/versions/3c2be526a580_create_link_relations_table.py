"""create link_relations table

Revision ID: 3c2be526a580
Revises: 8dd0ff5fc030
Create Date: 2025-11-24 03:05:34.241801

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3c2be526a580'
down_revision: Union[str, Sequence[str], None] = '8dd0ff5fc030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "link_relations",
        sa.Column("link_id", sa.UUID, primary_key=True),
        sa.Column("has_link_id", sa.UUID, primary_key=True),
        sa.UniqueConstraint("link_id", "has_link_id", name="uq_link_relations")
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("link_relations")
    pass
