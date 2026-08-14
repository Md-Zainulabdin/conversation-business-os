"""scope product sku and customer phone uniqueness per user

Revision ID: 010
Revises: 009
Create Date: 2026-08-14

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_products_sku"), table_name="products")
    op.create_index(
        op.f("ix_products_sku_user"), "products", ["user_id", "sku"], unique=True
    )

    op.drop_constraint("customers_phone_key", "customers", type_="unique")
    op.create_index(
        op.f("ix_customers_phone_user"), "customers", ["user_id", "phone"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_customers_phone_user"), table_name="customers")
    op.create_unique_constraint("customers_phone_key", "customers", ["phone"])

    op.drop_index(op.f("ix_products_sku_user"), table_name="products")
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)