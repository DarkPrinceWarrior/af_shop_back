import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    CurrencyCode,
    DeliveryPlace,
    Order,
    OrderCreate,
    OrderItem,
    Product,
    get_datetime_utc,
)


def _money_for_currency(
    *, currency: CurrencyCode, afn: Decimal, cny: Decimal, usd: Decimal
) -> Decimal:
    if currency == CurrencyCode.afn:
        return afn
    if currency == CurrencyCode.cny:
        return cny
    return usd


def _next_order_number() -> str:
    return f"SM-{get_datetime_utc().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def create_order_from_cart(*, session: Session, order_in: OrderCreate) -> Order:
    delivery_place = session.get(DeliveryPlace, order_in.delivery_place_id)
    if not delivery_place or not delivery_place.is_active:
        raise HTTPException(status_code=404, detail="Delivery place not found")

    product_ids = [item.product_id for item in order_in.items]
    products = session.exec(
        select(Product).where(Product.id.in_(product_ids))  # type: ignore[attr-defined]
    ).all()
    products_by_id = {product.id: product for product in products}

    subtotal = Decimal("0")
    order_items_data: list[dict[str, object]] = []

    for item_in in order_in.items:
        product = products_by_id.get(item_in.product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.stock_quantity < item_in.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Not enough stock for product {product.id}",
            )

        unit_price = _money_for_currency(
            currency=order_in.currency,
            afn=product.price_afn,
            cny=product.price_cny,
            usd=product.price_usd,
        )
        line_total = unit_price * item_in.quantity
        subtotal += line_total
        product.stock_quantity -= item_in.quantity
        session.add(product)
        order_items_data.append(
            {
                "product_id": product.id,
                "quantity": item_in.quantity,
                "product_name_en": product.name_en,
                "product_name_ps": product.name_ps,
                "product_name_zh_cn": product.name_zh_cn,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    delivery_fee = _money_for_currency(
        currency=order_in.currency,
        afn=delivery_place.fee_afn,
        cny=delivery_place.fee_cny,
        usd=delivery_place.fee_usd,
    )
    order = Order(
        order_number=_next_order_number(),
        customer_name=order_in.customer_name,
        customer_phone=order_in.customer_phone,
        customer_telegram=order_in.customer_telegram,
        customer_comment=order_in.customer_comment,
        language=order_in.language,
        currency=order_in.currency,
        delivery_place_id=order_in.delivery_place_id,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=subtotal + delivery_fee,
    )
    session.add(order)
    session.flush()

    for item_data in order_items_data:
        session.add(OrderItem(order_id=order.id, **item_data))

    session.commit()
    session.refresh(order)
    return order
