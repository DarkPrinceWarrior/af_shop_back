import shutil
import uuid
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, UploadFile, WebSocket
from fastapi.websockets import WebSocketDisconnect
from sqlalchemy import or_
from sqlmodel import Session, col, func, select

from app.api.deps import SessionDep, SuperuserDep, get_user_from_token
from app.core.config import settings
from app.core.db import engine
from app.models import (
    AdminDashboardPublic,
    CategoriesPublic,
    Category,
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
    DeliveryPlace,
    DeliveryPlaceCreate,
    DeliveryPlacePublic,
    DeliveryPlacesPublic,
    DeliveryPlaceUpdate,
    MediaUploadPublic,
    Message,
    Order,
    OrderAdminCommentUpdate,
    OrderCancel,
    OrderComplete,
    OrderPublic,
    OrdersPublic,
    OrderStatus,
    OrderStatusUpdate,
    Product,
    ProductCreate,
    ProductImage,
    ProductImageCreate,
    ProductImagePublic,
    ProductPublic,
    ProductsPublic,
    ProductUpdate,
    get_datetime_utc,
)
from app.services.orders import cancel_order, complete_order, update_order_status
from app.services.realtime import order_connection_manager

router = APIRouter(prefix="/admin", tags=["admin"])


def _save_upload_file(*, upload_file: UploadFile, folder: str) -> str:
    if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")
    suffix = Path(upload_file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image extension")

    media_root = Path(settings.MEDIA_ROOT)
    target_dir = media_root / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    target_path = target_dir / filename
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return f"{settings.MEDIA_URL.rstrip('/')}/{folder}/{filename}"


@router.get("/dashboard", response_model=AdminDashboardPublic)
def read_dashboard(session: SessionDep, _admin: SuperuserDep) -> AdminDashboardPublic:
    products_count = session.exec(select(func.count()).select_from(Product)).one()
    active_products_count = session.exec(
        select(func.count()).select_from(Product).where(Product.is_active)
    ).one()
    low_stock_products_count = session.exec(
        select(func.count())
        .select_from(Product)
        .where(Product.stock_quantity <= 5)
    ).one()
    delivery_places_count = session.exec(
        select(func.count()).select_from(DeliveryPlace)
    ).one()
    active_delivery_places_count = session.exec(
        select(func.count())
        .select_from(DeliveryPlace)
        .where(DeliveryPlace.is_active)
    ).one()
    new_orders_count = session.exec(
        select(func.count()).select_from(Order).where(Order.status == OrderStatus.new)
    ).one()
    active_orders_count = session.exec(
        select(func.count())
        .select_from(Order)
        .where(
            col(Order.status).in_(
                [
                    OrderStatus.new,
                    OrderStatus.accepted,
                    OrderStatus.preparing,
                    OrderStatus.delivering,
                ]
            )
        )
    ).one()
    return AdminDashboardPublic(
        products_count=products_count,
        active_products_count=active_products_count,
        low_stock_products_count=low_stock_products_count,
        delivery_places_count=delivery_places_count,
        active_delivery_places_count=active_delivery_places_count,
        new_orders_count=new_orders_count,
        active_orders_count=active_orders_count,
    )


@router.post("/media/images", response_model=MediaUploadPublic)
def upload_image(_admin: SuperuserDep, file: UploadFile) -> MediaUploadPublic:
    return MediaUploadPublic(image_path=_save_upload_file(upload_file=file, folder="images"))


@router.get("/categories", response_model=CategoriesPublic)
def read_categories(
    session: SessionDep,
    _admin: SuperuserDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> CategoriesPublic:
    count = session.exec(select(func.count()).select_from(Category)).one()
    statement = (
        select(Category)
        .order_by(col(Category.sort_order), col(Category.name_en))
        .offset(skip)
        .limit(limit)
    )
    return CategoriesPublic(data=session.exec(statement).all(), count=count)


@router.post("/categories", response_model=CategoryPublic)
def create_category(
    session: SessionDep, _admin: SuperuserDep, category_in: CategoryCreate
) -> Category:
    category = Category.model_validate(category_in)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryPublic)
def update_category(
    session: SessionDep,
    _admin: SuperuserDep,
    category_id: uuid.UUID,
    category_in: CategoryUpdate,
) -> Category:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.sqlmodel_update(category_in.model_dump(exclude_unset=True))
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    session: SessionDep, _admin: SuperuserDep, category_id: uuid.UUID
) -> Message:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(category)
    session.commit()
    return Message(message="Category deleted successfully")


@router.get("/products", response_model=ProductsPublic)
def read_products(
    session: SessionDep,
    _admin: SuperuserDep,
    category_id: uuid.UUID | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> ProductsPublic:
    filters = []
    if category_id:
        filters.append(Product.category_id == category_id)
    if q:
        search = f"%{q}%"
        filters.append(col(Product.name_en).ilike(search))
    count = session.exec(select(func.count()).select_from(Product).where(*filters)).one()
    statement = (
        select(Product)
        .where(*filters)
        .order_by(col(Product.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return ProductsPublic(data=session.exec(statement).all(), count=count)


@router.post("/products", response_model=ProductPublic)
def create_product(
    session: SessionDep, _admin: SuperuserDep, product_in: ProductCreate
) -> Product:
    category = session.get(Category, product_in.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    product_data = product_in.model_dump(exclude={"primary_image_path"})
    product = Product.model_validate(product_data)
    session.add(product)
    session.flush()
    if product_in.primary_image_path:
        session.add(
            ProductImage(
                product_id=product.id,
                image_path=product_in.primary_image_path,
                sort_order=0,
            )
        )
    session.commit()
    session.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductPublic)
def update_product(
    session: SessionDep,
    _admin: SuperuserDep,
    product_id: uuid.UUID,
    product_in: ProductUpdate,
) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = product_in.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        category = session.get(Category, update_data["category_id"])
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    product.sqlmodel_update(update_data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.post("/products/{product_id}/images", response_model=ProductImagePublic)
def create_product_image(
    session: SessionDep,
    _admin: SuperuserDep,
    product_id: uuid.UUID,
    image_in: ProductImageCreate,
) -> ProductImage:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    image = ProductImage.model_validate(image_in, update={"product_id": product_id})
    session.add(image)
    session.commit()
    session.refresh(image)
    return image


@router.delete("/products/{product_id}")
def delete_product(
    session: SessionDep, _admin: SuperuserDep, product_id: uuid.UUID
) -> Message:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return Message(message="Product deleted successfully")


@router.get("/delivery-places", response_model=DeliveryPlacesPublic)
def read_delivery_places(
    session: SessionDep,
    _admin: SuperuserDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> DeliveryPlacesPublic:
    count = session.exec(select(func.count()).select_from(DeliveryPlace)).one()
    statement = (
        select(DeliveryPlace)
        .order_by(col(DeliveryPlace.sort_order), col(DeliveryPlace.name_en))
        .offset(skip)
        .limit(limit)
    )
    return DeliveryPlacesPublic(data=session.exec(statement).all(), count=count)


@router.post("/delivery-places", response_model=DeliveryPlacePublic)
def create_delivery_place(
    session: SessionDep, _admin: SuperuserDep, place_in: DeliveryPlaceCreate
) -> DeliveryPlace:
    place = DeliveryPlace.model_validate(place_in)
    session.add(place)
    session.commit()
    session.refresh(place)
    return place


@router.patch("/delivery-places/{place_id}", response_model=DeliveryPlacePublic)
def update_delivery_place(
    session: SessionDep,
    _admin: SuperuserDep,
    place_id: uuid.UUID,
    place_in: DeliveryPlaceUpdate,
) -> DeliveryPlace:
    place = session.get(DeliveryPlace, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Delivery place not found")
    place.sqlmodel_update(place_in.model_dump(exclude_unset=True))
    session.add(place)
    session.commit()
    session.refresh(place)
    return place


@router.delete("/delivery-places/{place_id}")
def delete_delivery_place(
    session: SessionDep, _admin: SuperuserDep, place_id: uuid.UUID
) -> Message:
    place = session.get(DeliveryPlace, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Delivery place not found")
    session.delete(place)
    session.commit()
    return Message(message="Delivery place deleted successfully")


@router.get("/orders", response_model=OrdersPublic)
def read_orders(
    session: SessionDep,
    _admin: SuperuserDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    status: Annotated[OrderStatus | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=128)] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> OrdersPublic:
    filters = []
    if status is not None:
        filters.append(Order.status == status)
    stripped_q = q.strip() if q else None
    if stripped_q:
        query = f"%{stripped_q}%"
        filters.append(
            or_(
                col(Order.order_number).ilike(query),
                col(Order.customer_name).ilike(query),
                col(Order.customer_phone).ilike(query),
                col(Order.customer_telegram).ilike(query),
            )
        )
    if date_from is not None:
        filters.append(
            Order.created_at >= datetime.combine(date_from, time.min, timezone.utc)
        )
    if date_to is not None:
        filters.append(
            Order.created_at <= datetime.combine(date_to, time.max, timezone.utc)
        )

    count = session.exec(select(func.count()).select_from(Order).where(*filters)).one()
    statement = (
        select(Order)
        .where(*filters)
        .order_by(col(Order.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return OrdersPublic(data=session.exec(statement).all(), count=count)


@router.get("/orders/{order_id}", response_model=OrderPublic)
def read_order(
    session: SessionDep,
    _admin: SuperuserDep,
    order_id: uuid.UUID,
) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}/status", response_model=OrderPublic)
def update_order_status_route(
    session: SessionDep,
    admin: SuperuserDep,
    order_id: uuid.UUID,
    status_in: OrderStatusUpdate,
) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return update_order_status(
        session=session,
        order=order,
        new_status=status_in.status,
        admin_user=admin,
        admin_comment=status_in.admin_comment,
    )


@router.patch("/orders/{order_id}/comment", response_model=OrderPublic)
def update_order_admin_comment(
    session: SessionDep,
    _admin: SuperuserDep,
    order_id: uuid.UUID,
    comment_in: OrderAdminCommentUpdate,
) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.admin_comment = comment_in.admin_comment
    order.updated_at = get_datetime_utc()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.post("/orders/{order_id}/cancel", response_model=OrderPublic)
def cancel_order_route(
    session: SessionDep,
    admin: SuperuserDep,
    order_id: uuid.UUID,
    cancel_in: OrderCancel,
) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return cancel_order(
        session=session,
        order=order,
        admin_user=admin,
        admin_comment=cancel_in.admin_comment,
    )


@router.post("/orders/{order_id}/complete", response_model=OrderPublic)
def complete_order_route(
    session: SessionDep,
    admin: SuperuserDep,
    order_id: uuid.UUID,
    complete_in: OrderComplete,
) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return complete_order(
        session=session,
        order=order,
        admin_user=admin,
        admin_comment=complete_in.admin_comment,
    )


@router.websocket("/orders/ws")
async def orders_websocket(
    websocket: WebSocket,
    token: Annotated[str | None, Query()] = None,
) -> None:
    if not token:
        await websocket.close(code=1008)
        return
    with Session(engine) as session:
        try:
            user = get_user_from_token(session=session, token=token)
        except HTTPException:
            await websocket.close(code=1008)
            return
        if not user.is_superuser:
            await websocket.close(code=1008)
            return

    await order_connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        order_connection_manager.disconnect(websocket)
