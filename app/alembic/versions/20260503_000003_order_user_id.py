"""Add optional user ownership to orders

Revision ID: 20260503_000003
Revises: 20260430_000002
Create Date: 2026-05-03 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260503_000003"
down_revision = "20260430_000002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shop_order",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(op.f("ix_shop_order_user_id"), "shop_order", ["user_id"])
    op.create_foreign_key(
        op.f("fk_shop_order_user_id_user"),
        "shop_order",
        "user",
        ["user_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        op.f("fk_shop_order_user_id_user"),
        "shop_order",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_shop_order_user_id"), table_name="shop_order")
    op.drop_column("shop_order", "user_id")
