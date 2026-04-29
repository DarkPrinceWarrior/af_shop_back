"""Add order status workflow fields

Revision ID: 20260430_000002
Revises: 20260430_000001
Create Date: 2026-04-30 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260430_000002"
down_revision = "20260430_000001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shop_order",
        sa.Column("admin_comment", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "shop_order",
        sa.Column("stock_returned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "order_status_history",
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.String(length=1000), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["shop_order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_order_status_history_order_id"),
        "order_status_history",
        ["order_id"],
    )


def downgrade():
    op.drop_index(
        op.f("ix_order_status_history_order_id"),
        table_name="order_status_history",
    )
    op.drop_table("order_status_history")
    op.drop_column("shop_order", "stock_returned_at")
    op.drop_column("shop_order", "admin_comment")
