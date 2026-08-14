"""add sale_items and purchase_items, normalize multi-product

Revision ID: 008
Revises: 0a28dc092b2a
Create Date: 2026-08-12

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "008"
down_revision: str | None = "0a28dc092b2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sale_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sale_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_items_product_id"), "sale_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_sale_items_sale_id"), "sale_items", ["sale_id"], unique=False)

    op.create_table(
        "purchase_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("purchase_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("purchase_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_purchase_items_product_id"), "purchase_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_purchase_items_purchase_id"), "purchase_items", ["purchase_id"], unique=False)

    op.execute(
        """INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price, total_amount, created_at)
           SELECT gen_random_uuid(), id, product_id, quantity, unit_price, total_amount, created_at
           FROM sales"""
    )
    op.execute(
        """INSERT INTO purchase_items (id, purchase_id, product_id, quantity, purchase_price, total_amount, created_at)
           SELECT gen_random_uuid(), id, product_id, quantity, purchase_price, total_amount, created_at
           FROM purchases"""
    )

    op.drop_index(op.f("ix_sales_product_id"), table_name="sales")
    op.drop_index(op.f("ix_purchases_product_id"), table_name="purchases")
    op.drop_column("sales", "product_id")
    op.drop_column("sales", "quantity")
    op.drop_column("sales", "unit_price")
    op.drop_column("purchases", "product_id")
    op.drop_column("purchases", "quantity")
    op.drop_column("purchases", "purchase_price")


def downgrade() -> None:
    op.add_column("purchases", sa.Column("purchase_price", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("purchases", sa.Column("quantity", sa.Integer(), nullable=True))
    op.add_column("purchases", sa.Column("product_id", sa.Uuid(), nullable=True))
    op.add_column("sales", sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("sales", sa.Column("quantity", sa.Integer(), nullable=True))
    op.add_column("sales", sa.Column("product_id", sa.Uuid(), nullable=True))

    op.execute(
        """UPDATE sales AS s
           SET product_id = i.product_id, quantity = i.quantity, unit_price = i.unit_price
           FROM sale_items AS i WHERE i.sale_id = s.id"""
    )
    op.execute(
        """UPDATE purchases AS p
           SET product_id = i.product_id, quantity = i.quantity, purchase_price = i.purchase_price
           FROM purchase_items AS i WHERE i.purchase_id = p.id"""
    )

    op.create_index(op.f("ix_purchases_product_id"), "purchases", ["product_id"], unique=False)
    op.create_index(op.f("ix_sales_product_id"), "sales", ["product_id"], unique=False)
    op.drop_index(op.f("ix_purchase_items_purchase_id"), table_name="purchase_items")
    op.drop_index(op.f("ix_purchase_items_product_id"), table_name="purchase_items")
    op.drop_table("purchase_items")
    op.drop_index(op.f("ix_sale_items_sale_id"), table_name="sale_items")
    op.drop_index(op.f("ix_sale_items_product_id"), table_name="sale_items")
    op.drop_table("sale_items")