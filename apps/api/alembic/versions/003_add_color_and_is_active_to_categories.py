from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("color", sa.String(7), nullable=True))
    op.add_column(
        "categories",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("categories", "is_active")
    op.drop_column("categories", "color")
