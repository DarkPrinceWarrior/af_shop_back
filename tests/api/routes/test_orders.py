import uuid
from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    Category,
    DeliveryPlace,
    OrderStatus,
    OrderStatusHistory,
    Product,
)


def _create_shop_data(
    db: Session,
    *,
    stock_quantity: int = 5,
) -> tuple[Product, DeliveryPlace]:
    suffix = uuid.uuid4().hex
    category = Category(
        name_en=f"Test category {suffix}",
        name_ps=f"Test category PS {suffix}",
        name_zh_cn=f"Test category ZH {suffix}",
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    product = Product(
        name_en=f"Test product {suffix}",
        name_ps=f"Test product PS {suffix}",
        name_zh_cn=f"Test product ZH {suffix}",
        description_en="Test product description",
        description_ps="Test product description PS",
        description_zh_cn="Test product description ZH",
        sku=f"TEST-{suffix}",
        category_id=category.id,
        stock_quantity=stock_quantity,
        is_active=True,
        price_afn=Decimal("100.00"),
        price_cny=Decimal("10.00"),
        price_usd=Decimal("2.00"),
    )
    delivery_place = DeliveryPlace(
        name_en=f"Test delivery {suffix}",
        name_ps=f"Test delivery PS {suffix}",
        name_zh_cn=f"Test delivery ZH {suffix}",
        description_en="Test delivery description",
        description_ps="Test delivery description PS",
        description_zh_cn="Test delivery description ZH",
        image_path=f"/media/images/test-{suffix}.jpg",
        fee_afn=Decimal("20.00"),
        fee_cny=Decimal("2.00"),
        fee_usd=Decimal("1.00"),
        is_active=True,
    )
    db.add(product)
    db.add(delivery_place)
    db.commit()
    db.refresh(product)
    db.refresh(delivery_place)
    return product, delivery_place


def _order_payload(
    *,
    product: Product,
    delivery_place: DeliveryPlace,
    quantity: int = 2,
) -> dict[str, object]:
    return {
        "customer_name": "Workflow Test Customer",
        "customer_phone": "+93000000000",
        "customer_telegram": "@workflow_test",
        "customer_comment": "Test order",
        "language": "en",
        "currency": "AFN",
        "delivery_place_id": str(delivery_place.id),
        "items": [
            {
                "product_id": str(product.id),
                "quantity": quantity,
            }
        ],
    }


def _create_order(
    client: TestClient,
    *,
    product: Product,
    delivery_place: DeliveryPlace,
    quantity: int = 2,
) -> dict[str, object]:
    with patch("app.api.routes.catalog.send_order_notification"):
        response = client.post(
            f"{settings.API_V1_STR}/catalog/orders",
            json=_order_payload(
                product=product,
                delivery_place=delivery_place,
                quantity=quantity,
            ),
        )
    assert response.status_code == 200
    return response.json()


def _status_history(db: Session, order_id: str) -> list[OrderStatusHistory]:
    return list(
        db.exec(
            select(OrderStatusHistory).where(
                OrderStatusHistory.order_id == uuid.UUID(order_id)
            )
        ).all()
    )


def test_create_order_reduces_stock_and_records_initial_history(
    client: TestClient,
    db: Session,
) -> None:
    product, delivery_place = _create_shop_data(db, stock_quantity=5)

    order = _create_order(
        client,
        product=product,
        delivery_place=delivery_place,
        quantity=2,
    )

    db.expire_all()
    updated_product = db.get(Product, product.id)
    assert updated_product
    assert updated_product.stock_quantity == 3

    assert order["status"] == OrderStatus.new
    assert order["subtotal"] == "200.00"
    assert order["delivery_fee"] == "20.00"
    assert order["total"] == "220.00"

    history = _status_history(db, str(order["id"]))
    assert len(history) == 1
    assert history[0].old_status is None
    assert history[0].new_status == OrderStatus.new


def test_cancel_order_returns_stock_only_once(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    product, delivery_place = _create_shop_data(db, stock_quantity=5)
    order = _create_order(
        client,
        product=product,
        delivery_place=delivery_place,
        quantity=2,
    )

    response = client.post(
        f"{settings.API_V1_STR}/admin/orders/{order['id']}/cancel",
        headers=superuser_token_headers,
        json={"admin_comment": "Customer cancelled"},
    )
    assert response.status_code == 200
    cancelled_order = response.json()
    assert cancelled_order["status"] == OrderStatus.cancelled
    assert cancelled_order["admin_comment"] == "Customer cancelled"
    assert cancelled_order["stock_returned_at"] is not None

    db.expire_all()
    updated_product = db.get(Product, product.id)
    assert updated_product
    assert updated_product.stock_quantity == 5

    second_response = client.post(
        f"{settings.API_V1_STR}/admin/orders/{order['id']}/cancel",
        headers=superuser_token_headers,
        json={"admin_comment": "Duplicate cancel"},
    )
    assert second_response.status_code == 200

    db.expire_all()
    updated_product = db.get(Product, product.id)
    assert updated_product
    assert updated_product.stock_quantity == 5


def test_completed_order_cannot_be_cancelled(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    product, delivery_place = _create_shop_data(db, stock_quantity=5)
    order = _create_order(
        client,
        product=product,
        delivery_place=delivery_place,
        quantity=2,
    )

    complete_response = client.post(
        f"{settings.API_V1_STR}/admin/orders/{order['id']}/complete",
        headers=superuser_token_headers,
        json={"admin_comment": "Delivered and paid"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == OrderStatus.completed

    cancel_response = client.post(
        f"{settings.API_V1_STR}/admin/orders/{order['id']}/cancel",
        headers=superuser_token_headers,
        json={"admin_comment": "Too late"},
    )
    assert cancel_response.status_code == 409

    db.expire_all()
    updated_product = db.get(Product, product.id)
    assert updated_product
    assert updated_product.stock_quantity == 3


def test_cancelled_order_cannot_be_completed(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    product, delivery_place = _create_shop_data(db, stock_quantity=5)
    order = _create_order(
        client,
        product=product,
        delivery_place=delivery_place,
        quantity=2,
    )

    cancel_response = client.post(
        f"{settings.API_V1_STR}/admin/orders/{order['id']}/cancel",
        headers=superuser_token_headers,
        json={"admin_comment": "Customer cancelled"},
    )
    assert cancel_response.status_code == 200

    complete_response = client.post(
        f"{settings.API_V1_STR}/admin/orders/{order['id']}/complete",
        headers=superuser_token_headers,
        json={"admin_comment": "Cannot complete"},
    )
    assert complete_response.status_code == 409
