"""add user_id to products (scope catalog per business)

Revision ID: 009
Revises: 008
Create Date: 2026-08-12

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_products_user_id"), "products", ["user_id"], unique=False)

    # Existing rows have no owner; assign them to the first user so existing
    # environments keep working. Rows with no users remain invisible (NULL).
    op.execute(
        """UPDATE products
           SET user_id = (SELECT id FROM users ORDER BY created_at LIMIT 1)
           WHERE user_id IS NULL"""
    )

    op.alter_column("products", "user_id", nullable=False)
    op.create_foreign_key("fk_products_user_id", "products", "users", ["user_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint("fk_products_user_id", "products", type_="foreignkey")
    op.drop_index(op.f("ix_products_user_id"), table_name="products")
    op.drop_column("products", "user_id")