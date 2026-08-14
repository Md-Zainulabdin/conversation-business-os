from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # gen_random_uuid() is built-in since PostgreSQL 13
    # Using UUID type via postgresql dialect for reliability

    # --- users table ---
    op.add_column("users", sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE users SET uuid = gen_random_uuid()")
    op.alter_column("users", "uuid", nullable=False)

    op.drop_constraint("users_pkey", "users", type_="primary")
    op.drop_column("users", "id")

    op.alter_column("users", "uuid", new_column_name="id")
    op.create_primary_key("users_pkey", "users", ["id"])

    # --- categories table ---
    op.add_column("categories", sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE categories SET uuid = gen_random_uuid()")
    op.alter_column("categories", "uuid", nullable=False)

    op.drop_constraint("categories_pkey", "categories", type_="primary")
    op.drop_column("categories", "id")

    op.alter_column("categories", "uuid", new_column_name="id")
    op.create_primary_key("categories_pkey", "categories", ["id"])


def downgrade() -> None:
    # Converting UUID back to Integer is destructive.
    # This exists for dev rollback only; do not run on production.

    # --- users table ---
    op.add_column("users", sa.Column("id_int", sa.Integer(), nullable=True))
    op.execute("""
        UPDATE users SET id_int = sub.rn FROM (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn FROM users
        ) sub WHERE users.id = sub.id
    """)
    op.alter_column("users", "id_int", nullable=False)

    op.drop_constraint("users_pkey", "users", type_="primary")
    op.drop_column("users", "id")

    op.alter_column("users", "id_int", new_column_name="id")
    op.create_primary_key("users_pkey", "users", ["id"])

    # --- categories table ---
    op.add_column("categories", sa.Column("id_int", sa.Integer(), nullable=True))
    op.execute("""
        UPDATE categories SET id_int = sub.rn FROM (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn FROM categories
        ) sub WHERE categories.id = sub.id
    """)
    op.alter_column("categories", "id_int", nullable=False)

    op.drop_constraint("categories_pkey", "categories", type_="primary")
    op.drop_column("categories", "id")

    op.alter_column("categories", "id_int", new_column_name="id")
    op.create_primary_key("categories_pkey", "categories", ["id"])
