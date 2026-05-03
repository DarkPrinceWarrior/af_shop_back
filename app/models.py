import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import EmailStr
from sqlalchemy import DateTime, Numeric, String
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class LanguageCode(str, Enum):
    en = "en"
    ps = "ps"
    zh_cn = "zh-CN"


class CurrencyCode(str, Enum):
    afn = "AFN"
    cny = "CNY"
    usd = "USD"


class OrderStatus(str, Enum):
    new = "new"
    accepted = "accepted"
    preparing = "preparing"
    delivering = "delivering"
    completed = "completed"
    cancelled = "cancelled"


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    orders: list["Order"] = Relationship(back_populates="user")


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class LocalizedNameMixin(SQLModel):
    name_en: str = Field(min_length=1, max_length=255)
    name_ps: str = Field(min_length=1, max_length=255)
    name_zh_cn: str = Field(min_length=1, max_length=255)


class LocalizedDescriptionMixin(SQLModel):
    description_en: str | None = Field(default=None, max_length=1000)
    description_ps: str | None = Field(default=None, max_length=1000)
    description_zh_cn: str | None = Field(default=None, max_length=1000)


class MoneyMixin(SQLModel):
    price_afn: Decimal = Field(
        ge=0,
        sa_type=Numeric(12, 2),  # type: ignore
    )
    price_cny: Decimal = Field(
        ge=0,
        sa_type=Numeric(12, 2),  # type: ignore
    )
    price_usd: Decimal = Field(
        ge=0,
        sa_type=Numeric(12, 2),  # type: ignore
    )


class CategoryBase(LocalizedNameMixin):
    sort_order: int = Field(default=0, index=True)
    is_active: bool = Field(default=True, index=True)


class Category(CategoryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    products: list["Product"] = Relationship(back_populates="category")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    name_en: str | None = Field(default=None, min_length=1, max_length=255)
    name_ps: str | None = Field(default=None, min_length=1, max_length=255)
    name_zh_cn: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryPublic(CategoryBase):
    id: uuid.UUID
    created_at: datetime | None = None


class CategoriesPublic(SQLModel):
    data: list[CategoryPublic]
    count: int


class ProductBase(LocalizedNameMixin, LocalizedDescriptionMixin, MoneyMixin):
    sku: str | None = Field(default=None, max_length=100, index=True)
    category_id: uuid.UUID = Field(foreign_key="category.id", index=True)
    stock_quantity: int = Field(default=0, ge=0, index=True)
    is_active: bool = Field(default=True, index=True)


class Product(ProductBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    category: Category | None = Relationship(back_populates="products")
    images: list["ProductImage"] = Relationship(
        back_populates="product", cascade_delete=True
    )


class ProductCreate(ProductBase):
    primary_image_path: str | None = Field(default=None, max_length=500)


class ProductUpdate(SQLModel):
    name_en: str | None = Field(default=None, min_length=1, max_length=255)
    name_ps: str | None = Field(default=None, min_length=1, max_length=255)
    name_zh_cn: str | None = Field(default=None, min_length=1, max_length=255)
    description_en: str | None = Field(default=None, max_length=1000)
    description_ps: str | None = Field(default=None, max_length=1000)
    description_zh_cn: str | None = Field(default=None, max_length=1000)
    sku: str | None = Field(default=None, max_length=100)
    category_id: uuid.UUID | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    price_afn: Decimal | None = Field(default=None, ge=0)
    price_cny: Decimal | None = Field(default=None, ge=0)
    price_usd: Decimal | None = Field(default=None, ge=0)


class ProductImageBase(SQLModel):
    image_path: str = Field(max_length=500)
    alt_en: str | None = Field(default=None, max_length=255)
    alt_ps: str | None = Field(default=None, max_length=255)
    alt_zh_cn: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, index=True)


class ProductImage(ProductImageBase, table=True):
    __tablename__ = "product_image"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(
        foreign_key="product.id", nullable=False, ondelete="CASCADE", index=True
    )
    product: Product | None = Relationship(back_populates="images")


class ProductImageCreate(ProductImageBase):
    pass


class ProductImagePublic(ProductImageBase):
    id: uuid.UUID
    product_id: uuid.UUID


class ProductPublic(ProductBase):
    id: uuid.UUID
    created_at: datetime | None = None
    images: list[ProductImagePublic] = []


class ProductsPublic(SQLModel):
    data: list[ProductPublic]
    count: int


class DeliveryPlaceBase(LocalizedNameMixin, LocalizedDescriptionMixin):
    image_path: str = Field(max_length=500)
    fee_afn: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    fee_cny: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    fee_usd: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    sort_order: int = Field(default=0, index=True)
    is_active: bool = Field(default=True, index=True)


class DeliveryPlace(DeliveryPlaceBase, table=True):
    __tablename__ = "delivery_place"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    orders: list["Order"] = Relationship(back_populates="delivery_place")


class DeliveryPlaceCreate(DeliveryPlaceBase):
    pass


class DeliveryPlaceUpdate(SQLModel):
    name_en: str | None = Field(default=None, min_length=1, max_length=255)
    name_ps: str | None = Field(default=None, min_length=1, max_length=255)
    name_zh_cn: str | None = Field(default=None, min_length=1, max_length=255)
    description_en: str | None = Field(default=None, max_length=1000)
    description_ps: str | None = Field(default=None, max_length=1000)
    description_zh_cn: str | None = Field(default=None, max_length=1000)
    image_path: str | None = Field(default=None, max_length=500)
    fee_afn: Decimal | None = Field(default=None, ge=0)
    fee_cny: Decimal | None = Field(default=None, ge=0)
    fee_usd: Decimal | None = Field(default=None, ge=0)
    sort_order: int | None = None
    is_active: bool | None = None


class DeliveryPlacePublic(DeliveryPlaceBase):
    id: uuid.UUID
    created_at: datetime | None = None


class DeliveryPlacesPublic(SQLModel):
    data: list[DeliveryPlacePublic]
    count: int


class CatalogCategoryPublic(SQLModel):
    id: uuid.UUID
    name: str
    sort_order: int
    is_active: bool


class CatalogProductImagePublic(SQLModel):
    id: uuid.UUID
    image_path: str
    alt: str | None = None
    sort_order: int


class CatalogProductPublic(SQLModel):
    id: uuid.UUID
    category_id: uuid.UUID
    sku: str | None = None
    name: str
    description: str | None = None
    price: Decimal
    currency: CurrencyCode
    stock_quantity: int
    is_active: bool
    images: list[CatalogProductImagePublic] = []


class CatalogDeliveryPlacePublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    image_path: str
    delivery_fee: Decimal
    currency: CurrencyCode
    sort_order: int
    is_active: bool


class CatalogBootstrapPublic(SQLModel):
    language: LanguageCode
    currency: CurrencyCode
    languages: list[LanguageCode]
    currencies: list[CurrencyCode]
    categories: list[CatalogCategoryPublic]
    products: list[CatalogProductPublic]
    delivery_places: list[CatalogDeliveryPlacePublic]


class OrderBase(SQLModel):
    customer_name: str = Field(min_length=1, max_length=255)
    customer_phone: str = Field(min_length=3, max_length=64)
    customer_telegram: str | None = Field(default=None, max_length=128)
    customer_comment: str | None = Field(default=None, max_length=1000)
    language: LanguageCode = Field(
        default=LanguageCode.en,
        sa_type=String(length=16),  # type: ignore
    )
    currency: CurrencyCode = Field(
        default=CurrencyCode.afn,
        sa_type=String(length=3),  # type: ignore
    )
    delivery_place_id: uuid.UUID = Field(foreign_key="delivery_place.id", index=True)


class Order(OrderBase, table=True):
    __tablename__ = "shop_order"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    order_number: str = Field(unique=True, index=True, max_length=32)
    status: OrderStatus = Field(
        default=OrderStatus.new,
        index=True,
        sa_type=String(length=32),  # type: ignore
    )
    admin_comment: str | None = Field(default=None, max_length=1000)
    stock_returned_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    subtotal: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    delivery_fee: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    total: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    delivery_place: DeliveryPlace | None = Relationship(back_populates="orders")
    user: User | None = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order", cascade_delete=True)
    status_history: list["OrderStatusHistory"] = Relationship(
        back_populates="order", cascade_delete=True
    )


class OrderItemBase(SQLModel):
    product_id: uuid.UUID = Field(foreign_key="product.id", index=True)
    quantity: int = Field(gt=0)


class OrderItem(OrderItemBase, table=True):
    __tablename__ = "order_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(
        foreign_key="shop_order.id", nullable=False, ondelete="CASCADE", index=True
    )
    product_name_en: str = Field(max_length=255)
    product_name_ps: str = Field(max_length=255)
    product_name_zh_cn: str = Field(max_length=255)
    unit_price: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    line_total: Decimal = Field(ge=0, sa_type=Numeric(12, 2))  # type: ignore
    order: Order | None = Relationship(back_populates="items")
    product: Product | None = Relationship()


class OrderItemCreate(OrderItemBase):
    pass


class OrderCreate(OrderBase):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusHistoryBase(SQLModel):
    old_status: OrderStatus | None = Field(
        default=None,
        sa_type=String(length=32),  # type: ignore
    )
    new_status: OrderStatus = Field(
        sa_type=String(length=32),  # type: ignore
    )
    comment: str | None = Field(default=None, max_length=1000)


class OrderStatusHistory(OrderStatusHistoryBase, table=True):
    __tablename__ = "order_status_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(
        foreign_key="shop_order.id", nullable=False, ondelete="CASCADE", index=True
    )
    changed_by_user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    order: Order | None = Relationship(back_populates="status_history")


class OrderQuoteItemPublic(SQLModel):
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderQuotePublic(SQLModel):
    currency: CurrencyCode
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    items: list[OrderQuoteItemPublic]


class OrderItemPublic(SQLModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name_en: str
    product_name_ps: str
    product_name_zh_cn: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderStatusHistoryPublic(SQLModel):
    id: uuid.UUID
    old_status: OrderStatus | None = None
    new_status: OrderStatus
    comment: str | None = None
    changed_by_user_id: uuid.UUID | None = None
    created_at: datetime | None = None


class OrderPublic(OrderBase):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    order_number: str
    status: OrderStatus
    admin_comment: str | None = None
    stock_returned_at: datetime | None = None
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None
    items: list[OrderItemPublic] = []
    status_history: list[OrderStatusHistoryPublic] = []


class OrdersPublic(SQLModel):
    data: list[OrderPublic]
    count: int


class AdminDashboardPublic(SQLModel):
    products_count: int
    active_products_count: int
    low_stock_products_count: int
    delivery_places_count: int
    active_delivery_places_count: int
    new_orders_count: int
    active_orders_count: int


class OrderStatusUpdate(SQLModel):
    status: OrderStatus
    admin_comment: str | None = Field(default=None, max_length=1000)


class OrderAdminCommentUpdate(SQLModel):
    admin_comment: str | None = Field(default=None, max_length=1000)


class OrderCancel(SQLModel):
    admin_comment: str | None = Field(default=None, max_length=1000)


class OrderComplete(SQLModel):
    admin_comment: str | None = Field(default=None, max_length=1000)


class MediaUploadPublic(SQLModel):
    image_path: str


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
