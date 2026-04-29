import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    CurrencyCode,
    DeliveryPlace,
    LanguageCode,
    Order,
    OrderCreate,
    OrderItem,
    OrderQuoteItemPublic,
    OrderQuotePublic,
    OrderStatus,
    OrderStatusHistory,
    Product,
    User,
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


def localized_name(
    *,
    language: LanguageCode,
    name_en: str,
    name_ps: str,
    name_zh_cn: str,
) -> str:
    if language == LanguageCode.ps:
        return name_ps
    if language == LanguageCode.zh_cn:
        return name_zh_cn
    return name_en


def localized_description(
    *,
    language: LanguageCode,
    description_en: str | None,
    description_ps: str | None,
    description_zh_cn: str | None,
) -> str | None:
    if language == LanguageCode.ps:
        return description_ps or description_en
    if language == LanguageCode.zh_cn:
        return description_zh_cn or description_en
    return description_en


def _next_order_number() -> str:
    return f"SM-{get_datetime_utc().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def build_order_quote(*, session: Session, order_in: OrderCreate) -> OrderQuotePublic:
    delivery_place = session.get(DeliveryPlace, order_in.delivery_place_id)
    if not delivery_place or not delivery_place.is_active:
        raise HTTPException(status_code=404, detail="Delivery place not found")

    product_ids = [item.product_id for item in order_in.items]
    products = session.exec(
        select(Product).where(Product.id.in_(product_ids))  # type: ignore[attr-defined]
    ).all()
    products_by_id = {product.id: product for product in products}

    subtotal = Decimal("0")
    quote_items: list[OrderQuoteItemPublic] = []

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
        quote_items.append(
            OrderQuoteItemPublic(
                product_id=product.id,
                product_name=localized_name(
                    language=order_in.language,
                    name_en=product.name_en,
                    name_ps=product.name_ps,
                    name_zh_cn=product.name_zh_cn,
                ),
                quantity=item_in.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    delivery_fee = _money_for_currency(
        currency=order_in.currency,
        afn=delivery_place.fee_afn,
        cny=delivery_place.fee_cny,
        usd=delivery_place.fee_usd,
    )
    return OrderQuotePublic(
        currency=order_in.currency,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=subtotal + delivery_fee,
        items=quote_items,
    )


def create_order_from_cart(*, session: Session, order_in: OrderCreate) -> Order:
    quote = build_order_quote(session=session, order_in=order_in)

    product_ids = [item.product_id for item in order_in.items]
    products = session.exec(
        select(Product).where(Product.id.in_(product_ids))  # type: ignore[attr-defined]
    ).all()
    products_by_id = {product.id: product for product in products}

    order_items_data: list[dict[str, object]] = []

    for item_in in order_in.items:
        product = products_by_id[item_in.product_id]
        product.stock_quantity -= item_in.quantity
        session.add(product)
        unit_price = _money_for_currency(
            currency=order_in.currency,
            afn=product.price_afn,
            cny=product.price_cny,
            usd=product.price_usd,
        )
        line_total = unit_price * item_in.quantity
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

    order = Order(
        order_number=_next_order_number(),
        customer_name=order_in.customer_name,
        customer_phone=order_in.customer_phone,
        customer_telegram=order_in.customer_telegram,
        customer_comment=order_in.customer_comment,
        language=order_in.language,
        currency=order_in.currency,
        delivery_place_id=order_in.delivery_place_id,
        subtotal=quote.subtotal,
        delivery_fee=quote.delivery_fee,
        total=quote.total,
    )
    session.add(order)
    session.flush()
    session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=None,
            new_status=OrderStatus.new,
            comment="Order created",
        )
    )

    for item_data in order_items_data:
        session.add(OrderItem(order_id=order.id, **item_data))

    session.commit()
    session.refresh(order)
    return order


def update_order_status(
    *,
    session: Session,
    order: Order,
    new_status: OrderStatus,
    admin_user: User,
    admin_comment: str | None = None,
) -> Order:
    old_status = order.status
    order.status = new_status
    if admin_comment is not None:
        order.admin_comment = admin_comment
    order.updated_at = get_datetime_utc()
    session.add(order)
    session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            comment=admin_comment,
            changed_by_user_id=admin_user.id,
        )
    )
    session.commit()
    session.refresh(order)
    return order


def cancel_order(
    *,
    session: Session,
    order: Order,
    admin_user: User,
    admin_comment: str | None = None,
) -> Order:
    if order.status == OrderStatus.completed:
        raise HTTPException(status_code=409, detail="Completed order cannot be cancelled")

    if order.stock_returned_at is None:
        for item in order.items:
            product = session.get(Product, item.product_id)
            if product:
                product.stock_quantity += item.quantity
                session.add(product)
        order.stock_returned_at = get_datetime_utc()

    return update_order_status(
        session=session,
        order=order,
        new_status=OrderStatus.cancelled,
        admin_user=admin_user,
        admin_comment=admin_comment,
    )


def complete_order(
    *,
    session: Session,
    order: Order,
    admin_user: User,
    admin_comment: str | None = None,
) -> Order:
    if order.status == OrderStatus.cancelled:
        raise HTTPException(status_code=409, detail="Cancelled order cannot be completed")
    return update_order_status(
        session=session,
        order=order,
        new_status=OrderStatus.completed,
        admin_user=admin_user,
        admin_comment=admin_comment,
    )
