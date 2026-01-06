"""add_indexes

Revision ID: 92fdbeb09994
Revises: 3c2be526a580
Create Date: 2025-11-28 05:21:46.406949

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '92fdbeb09994'
down_revision: Union[str, Sequence[str], None] = '3c2be526a580'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('idx_domains_name', 'domains', ['name'])
    op.create_index('idx_links_url', 'links', ['url'])
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
