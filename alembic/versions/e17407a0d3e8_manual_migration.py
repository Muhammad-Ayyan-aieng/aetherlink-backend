"""manual_migration

Revision ID: e17407a0d3e8
Revises: 288c1677657b
Create Date: 2026-07-07 06:13:20.047694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e17407a0d3e8'
down_revision: Union[str, None] = '288c1677657b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
