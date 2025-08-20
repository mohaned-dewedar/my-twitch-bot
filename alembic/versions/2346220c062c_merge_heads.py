"""merge_heads

Revision ID: 2346220c062c
Revises: 3cbb1e1e2f33, 8f6450b59673
Create Date: 2025-08-20 05:10:53.075283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2346220c062c'
down_revision: Union[str, Sequence[str], None] = ('3cbb1e1e2f33', '8f6450b59673')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
