"""description_of_changes

Revision ID: 288c1677657b
Revises: 9ef396061c69
Create Date: 2026-07-07 06:12:02.828693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '288c1677657b'
down_revision: Union[str, None] = '9ef396061c69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
