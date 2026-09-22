"""test_update

Revision ID: 87156c5f15f8
Revises:
Create Date: 2026-09-22 18:00:29.221045

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "87156c5f15f8"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "transmission_oil_cache",
        "end_end_year",
        new_column_name="end_year",
    )


def downgrade() -> None:
    op.alter_column(
        "transmission_oil_cache",
        "end_year",
        new_column_name="end_end_year",
    )