"""description_of_changes

Revision ID: 9ef396061c69
Revises: b947b7b20def
Create Date: 2026-07-07 06:11:12.233544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ef396061c69'
down_revision: Union[str, None] = 'b947b7b20def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
