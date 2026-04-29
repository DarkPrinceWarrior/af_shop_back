import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query
from sqlmodel import col, func, or_, select

from app.api.deps import SessionDep
from app.models import (
    CategoriesPublic,
    Category,
    DeliveryPlace,
    DeliveryPlacesPublic,
    OrderCreate,
    OrderPublic,
    Product,
    ProductsPublic,
)
from app.services.orders import create_order_from_cart
from app.services.realtime import order_connection_manager
from app.services.telegram import send_order_notification

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories", response_model=CategoriesPublic)
def read_public_categories(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> CategoriesPublic:
    count = session.exec(
        select(func.count()).select_from(Category).where(Category.is_active)
    ).one()
    statement = (
        select(Category)
        .where(Category.is_active)
        .order_by(col(Category.sort_order), col(Category.name_en))
        .offset(skip)
        .limit(limit)
    )
    return CategoriesPublic(data=session.exec(statement).all(), count=count)


@router.get("/products", response_model=ProductsPublic)
def read_public_products(
    session: SessionDep,
    category_id: uuid.UUID | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> ProductsPublic:
    filters = [Product.is_active]
    if category_id:
        filters.append(Product.category_id == category_id)
    if q:
        search = f"%{q}%"
        filters.append(
            or_(
                col(Product.name_en).ilike(search),
                col(Product.name_ps).ilike(search),
                col(Product.name_zh_cn).ilike(search),
                col(Product.sku).ilike(search),
            )
        )
    count = session.exec(
        select(func.count()).select_from(Product).where(*filters)
    ).one()
    statement = (
        select(Product)
        .where(*filters)
        .order_by(col(Product.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    products = session.exec(statement).all()
    return ProductsPublic(data=products, count=count)


@router.get("/delivery-places", response_model=DeliveryPlacesPublic)
def read_public_delivery_places(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> DeliveryPlacesPublic:
    count = session.exec(
        select(func.count()).select_from(DeliveryPlace).where(DeliveryPlace.is_active)
    ).one()
    statement = (
        select(DeliveryPlace)
        .where(DeliveryPlace.is_active)
        .order_by(col(DeliveryPlace.sort_order), col(DeliveryPlace.name_en))
        .offset(skip)
        .limit(limit)
    )
    return DeliveryPlacesPublic(data=session.exec(statement).all(), count=count)


@router.post("/orders", response_model=OrderPublic)
async def create_public_order(
    session: SessionDep,
    background_tasks: BackgroundTasks,
    order_in: OrderCreate,
) -> OrderPublic:
    order = create_order_from_cart(session=session, order_in=order_in)
    _ = order.items
    background_tasks.add_task(send_order_notification, order)
    await order_connection_manager.broadcast(
        {
            "type": "order.created",
            "order_id": str(order.id),
            "order_number": order.order_number,
            "total": str(order.total),
            "currency": order.currency.value,
        }
    )
    return OrderPublic.model_validate(order)
