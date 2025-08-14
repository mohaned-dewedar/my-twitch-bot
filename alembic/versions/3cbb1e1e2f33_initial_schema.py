"""initial schema

Revision ID: 3cbb1e1e2f33
Revises: 
Create Date: 2025-08-14 13:19:52.134681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cbb1e1e2f33'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with open("init/schema.sql", "r") as f:
        sql = f.read()
    op.execute(sql)


def downgrade() -> None:
    """Downgrade schema."""
    pass
