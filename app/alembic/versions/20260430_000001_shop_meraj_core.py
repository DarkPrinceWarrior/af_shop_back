"""Add Shop Meraj core commerce models

Revision ID: 20260430_000001
Revises: fe56fa70289e
Create Date: 2026-04-30 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260430_000001"
down_revision = "fe56fa70289e"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("item")

    op.create_table(
        "category",
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ps", sa.String(length=255), nullable=False),
        sa.Column("name_zh_cn", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_category_is_active"), "category", ["is_active"])
    op.create_index(op.f("ix_category_sort_order"), "category", ["sort_order"])

    op.create_table(
        "delivery_place",
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ps", sa.String(length=255), nullable=False),
        sa.Column("name_zh_cn", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.String(length=1000), nullable=True),
        sa.Column("description_ps", sa.String(length=1000), nullable=True),
        sa.Column("description_zh_cn", sa.String(length=1000), nullable=True),
        sa.Column("image_path", sa.String(length=500), nullable=False),
        sa.Column("fee_afn", sa.Numeric(12, 2), nullable=False),
        sa.Column("fee_cny", sa.Numeric(12, 2), nullable=False),
        sa.Column("fee_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_delivery_place_is_active"), "delivery_place", ["is_active"]
    )
    op.create_index(
        op.f("ix_delivery_place_sort_order"), "delivery_place", ["sort_order"]
    )

    op.create_table(
        "product",
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ps", sa.String(length=255), nullable=False),
        sa.Column("name_zh_cn", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.String(length=1000), nullable=True),
        sa.Column("description_ps", sa.String(length=1000), nullable=True),
        sa.Column("description_zh_cn", sa.String(length=1000), nullable=True),
        sa.Column("price_afn", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_cny", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_category_id"), "product", ["category_id"])
    op.create_index(op.f("ix_product_is_active"), "product", ["is_active"])
    op.create_index(op.f("ix_product_sku"), "product", ["sku"])
    op.create_index(op.f("ix_product_stock_quantity"), "product", ["stock_quantity"])

    op.create_table(
        "product_image",
        sa.Column("image_path", sa.String(length=500), nullable=False),
        sa.Column("alt_en", sa.String(length=255), nullable=True),
        sa.Column("alt_ps", sa.String(length=255), nullable=True),
        sa.Column("alt_zh_cn", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_image_product_id"), "product_image", ["product_id"])
    op.create_index(op.f("ix_product_image_sort_order"), "product_image", ["sort_order"])

    op.create_table(
        "shop_order",
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_phone", sa.String(length=64), nullable=False),
        sa.Column("customer_telegram", sa.String(length=128), nullable=True),
        sa.Column("customer_comment", sa.String(length=1000), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("delivery_place_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("delivery_fee", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["delivery_place_id"], ["delivery_place.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index(
        op.f("ix_shop_order_delivery_place_id"),
        "shop_order",
        ["delivery_place_id"],
    )
    op.create_index(op.f("ix_shop_order_order_number"), "shop_order", ["order_number"])
    op.create_index(op.f("ix_shop_order_status"), "shop_order", ["status"])

    op.create_table(
        "order_item",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_name_en", sa.String(length=255), nullable=False),
        sa.Column("product_name_ps", sa.String(length=255), nullable=False),
        sa.Column("product_name_zh_cn", sa.String(length=255), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["shop_order.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_item_order_id"), "order_item", ["order_id"])
    op.create_index(op.f("ix_order_item_product_id"), "order_item", ["product_id"])


def downgrade():
    op.drop_index(op.f("ix_order_item_product_id"), table_name="order_item")
    op.drop_index(op.f("ix_order_item_order_id"), table_name="order_item")
    op.drop_table("order_item")
    op.drop_index(op.f("ix_shop_order_status"), table_name="shop_order")
    op.drop_index(op.f("ix_shop_order_order_number"), table_name="shop_order")
    op.drop_index(
        op.f("ix_shop_order_delivery_place_id"), table_name="shop_order"
    )
    op.drop_table("shop_order")
    op.drop_index(op.f("ix_product_image_sort_order"), table_name="product_image")
    op.drop_index(op.f("ix_product_image_product_id"), table_name="product_image")
    op.drop_table("product_image")
    op.drop_index(op.f("ix_product_stock_quantity"), table_name="product")
    op.drop_index(op.f("ix_product_sku"), table_name="product")
    op.drop_index(op.f("ix_product_is_active"), table_name="product")
    op.drop_index(op.f("ix_product_category_id"), table_name="product")
    op.drop_table("product")
    op.drop_index(op.f("ix_delivery_place_sort_order"), table_name="delivery_place")
    op.drop_index(op.f("ix_delivery_place_is_active"), table_name="delivery_place")
    op.drop_table("delivery_place")
    op.drop_index(op.f("ix_category_sort_order"), table_name="category")
    op.drop_index(op.f("ix_category_is_active"), table_name="category")
    op.drop_table("category")

    op.create_table(
        "item",
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
