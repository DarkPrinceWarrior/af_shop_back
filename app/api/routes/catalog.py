import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query
from sqlmodel import col, func, or_, select

from app.api.deps import SessionDep
from app.models import (
    CatalogBootstrapPublic,
    CatalogCategoryPublic,
    CatalogDeliveryPlacePublic,
    CatalogProductImagePublic,
    CatalogProductPublic,
    CategoriesPublic,
    Category,
    CurrencyCode,
    DeliveryPlace,
    DeliveryPlacesPublic,
    LanguageCode,
    OrderCreate,
    OrderPublic,
    OrderQuotePublic,
    Product,
    ProductsPublic,
)
from app.services.orders import (
    _money_for_currency,
    build_order_quote,
    create_order_from_cart,
    localized_description,
    localized_name,
)
from app.services.realtime import order_connection_manager
from app.services.telegram import send_order_notification

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _catalog_category(category: Category, language: LanguageCode) -> CatalogCategoryPublic:
    return CatalogCategoryPublic(
        id=category.id,
        name=localized_name(
            language=language,
            name_en=category.name_en,
            name_ps=category.name_ps,
            name_zh_cn=category.name_zh_cn,
        ),
        sort_order=category.sort_order,
        is_active=category.is_active,
    )


def _catalog_product(
    product: Product, language: LanguageCode, currency: CurrencyCode
) -> CatalogProductPublic:
    return CatalogProductPublic(
        id=product.id,
        category_id=product.category_id,
        sku=product.sku,
        name=localized_name(
            language=language,
            name_en=product.name_en,
            name_ps=product.name_ps,
            name_zh_cn=product.name_zh_cn,
        ),
        description=localized_description(
            language=language,
            description_en=product.description_en,
            description_ps=product.description_ps,
            description_zh_cn=product.description_zh_cn,
        ),
        price=_money_for_currency(
            currency=currency,
            afn=product.price_afn,
            cny=product.price_cny,
            usd=product.price_usd,
        ),
        currency=currency,
        stock_quantity=product.stock_quantity,
        is_active=product.is_active,
        images=[
            CatalogProductImagePublic(
                id=image.id,
                image_path=image.image_path,
                alt=localized_description(
                    language=language,
                    description_en=image.alt_en,
                    description_ps=image.alt_ps,
                    description_zh_cn=image.alt_zh_cn,
                ),
                sort_order=image.sort_order,
            )
            for image in product.images
        ],
    )


def _catalog_delivery_place(
    place: DeliveryPlace, language: LanguageCode, currency: CurrencyCode
) -> CatalogDeliveryPlacePublic:
    return CatalogDeliveryPlacePublic(
        id=place.id,
        name=localized_name(
            language=language,
            name_en=place.name_en,
            name_ps=place.name_ps,
            name_zh_cn=place.name_zh_cn,
        ),
        description=localized_description(
            language=language,
            description_en=place.description_en,
            description_ps=place.description_ps,
            description_zh_cn=place.description_zh_cn,
        ),
        image_path=place.image_path,
        delivery_fee=_money_for_currency(
            currency=currency,
            afn=place.fee_afn,
            cny=place.fee_cny,
            usd=place.fee_usd,
        ),
        currency=currency,
        sort_order=place.sort_order,
        is_active=place.is_active,
    )


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


@router.get("/categories/view", response_model=list[CatalogCategoryPublic])
def read_public_categories_view(
    session: SessionDep,
    language: LanguageCode = LanguageCode.en,
) -> list[CatalogCategoryPublic]:
    statement = (
        select(Category)
        .where(Category.is_active)
        .order_by(col(Category.sort_order), col(Category.name_en))
    )
    return [
        _catalog_category(category, language)
        for category in session.exec(statement).all()
    ]


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


@router.get("/products/view", response_model=list[CatalogProductPublic])
def read_public_products_view(
    session: SessionDep,
    category_id: uuid.UUID | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    language: LanguageCode = LanguageCode.en,
    currency: CurrencyCode = CurrencyCode.afn,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[CatalogProductPublic]:
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
    statement = (
        select(Product)
        .where(*filters)
        .order_by(col(Product.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return [
        _catalog_product(product, language, currency)
        for product in session.exec(statement).all()
    ]


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


@router.get("/delivery-places/view", response_model=list[CatalogDeliveryPlacePublic])
def read_public_delivery_places_view(
    session: SessionDep,
    language: LanguageCode = LanguageCode.en,
    currency: CurrencyCode = CurrencyCode.afn,
) -> list[CatalogDeliveryPlacePublic]:
    statement = (
        select(DeliveryPlace)
        .where(DeliveryPlace.is_active)
        .order_by(col(DeliveryPlace.sort_order), col(DeliveryPlace.name_en))
    )
    return [
        _catalog_delivery_place(place, language, currency)
        for place in session.exec(statement).all()
    ]


@router.get("/bootstrap", response_model=CatalogBootstrapPublic)
def read_catalog_bootstrap(
    session: SessionDep,
    language: LanguageCode = LanguageCode.en,
    currency: CurrencyCode = CurrencyCode.afn,
) -> CatalogBootstrapPublic:
    categories = session.exec(
        select(Category)
        .where(Category.is_active)
        .order_by(col(Category.sort_order), col(Category.name_en))
    ).all()
    products = session.exec(
        select(Product)
        .where(Product.is_active)
        .order_by(col(Product.created_at).desc())
    ).all()
    delivery_places = session.exec(
        select(DeliveryPlace)
        .where(DeliveryPlace.is_active)
        .order_by(col(DeliveryPlace.sort_order), col(DeliveryPlace.name_en))
    ).all()
    return CatalogBootstrapPublic(
        language=language,
        currency=currency,
        languages=list(LanguageCode),
        currencies=list(CurrencyCode),
        categories=[
            _catalog_category(category, language)
            for category in categories
        ],
        products=[
            _catalog_product(product, language, currency)
            for product in products
        ],
        delivery_places=[
            _catalog_delivery_place(place, language, currency)
            for place in delivery_places
        ],
    )


@router.post("/orders/quote", response_model=OrderQuotePublic)
def quote_public_order(session: SessionDep, order_in: OrderCreate) -> OrderQuotePublic:
    return build_order_quote(session=session, order_in=order_in)


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
            "currency": _enum_value(order.currency),
        }
    )
    return OrderPublic.model_validate(order)
