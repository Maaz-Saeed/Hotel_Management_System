"""add booking overlap exclusion constraint

Revision ID: 1d9e7944e9c6
Revises: 1c16643145dc
Create Date: 2026-10-09 03:07:43.435086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d9e7944e9c6'
down_revision: Union[str, Sequence[str], None] = '1c16643145dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
        room_id WITH =, 
        daterange(check_in, check_out) WITH &&
        ) WHERE (status IN ('reserved', 'checked_in'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT no_overlapping_bookings")