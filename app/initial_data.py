import json
import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Category, DeliveryPlace, Product, ProductImage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _decimal(value: str | int | float) -> Decimal:
    return Decimal(str(value))


def _load_external_seed() -> dict[str, Any] | None:
    seed_file = os.getenv("SHOP_SEED_FILE") or "seed/shop_seed.json"
    seed_path = Path(seed_file)
    if not seed_path.exists():
        return None
    logger.info("Loading shop seed data from %s", seed_path)
    with seed_path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Shop seed file root must be a JSON object")
    return data


def _seed_categories_from_payload(
    session: Session, seed_data: dict[str, Any]
) -> dict[str, Category]:
    existing = session.exec(select(Category)).first()
    if existing:
        categories = session.exec(select(Category)).all()
        return {category.name_en: category for category in categories}

    categories = []
    for item in seed_data.get("categories", []):
        categories.append(
            Category(
                name_en=item["name_en"],
                name_ps=item["name_ps"],
                name_zh_cn=item["name_zh_cn"],
                sort_order=item.get("sort_order", 0),
                is_active=item.get("is_active", True),
            )
        )
    for category in categories:
        session.add(category)
    session.commit()
    return {category.name_en: category for category in categories}


def _seed_delivery_places_from_payload(
    session: Session, seed_data: dict[str, Any]
) -> None:
    existing = session.exec(select(DeliveryPlace)).first()
    if existing:
        return

    for item in seed_data.get("delivery_places", []):
        session.add(
            DeliveryPlace(
                name_en=item["name_en"],
                name_ps=item["name_ps"],
                name_zh_cn=item["name_zh_cn"],
                description_en=item.get("description_en"),
                description_ps=item.get("description_ps"),
                description_zh_cn=item.get("description_zh_cn"),
                image_path=item["image_path"],
                fee_afn=_decimal(item["fee_afn"]),
                fee_cny=_decimal(item["fee_cny"]),
                fee_usd=_decimal(item["fee_usd"]),
                sort_order=item.get("sort_order", 0),
                is_active=item.get("is_active", True),
            )
        )
    session.commit()


def _seed_products_from_payload(
    session: Session,
    seed_data: dict[str, Any],
    categories: dict[str, Category],
) -> None:
    existing = session.exec(select(Product)).first()
    if existing:
        return

    for item in seed_data.get("products", []):
        category_name = item["category_name_en"]
        category = categories.get(category_name)
        if not category:
            raise ValueError(f"Unknown product category: {category_name}")
        product = Product(
            name_en=item["name_en"],
            name_ps=item["name_ps"],
            name_zh_cn=item["name_zh_cn"],
            description_en=item.get("description_en"),
            description_ps=item.get("description_ps"),
            description_zh_cn=item.get("description_zh_cn"),
            sku=item.get("sku"),
            category_id=category.id,
            stock_quantity=item.get("stock_quantity", 0),
            is_active=item.get("is_active", True),
            price_afn=_decimal(item["price_afn"]),
            price_cny=_decimal(item["price_cny"]),
            price_usd=_decimal(item["price_usd"]),
        )
        session.add(product)
        session.flush()
        for image in item.get("images", []):
            session.add(
                ProductImage(
                    product_id=product.id,
                    image_path=image["image_path"],
                    alt_en=image.get("alt_en", product.name_en),
                    alt_ps=image.get("alt_ps", product.name_ps),
                    alt_zh_cn=image.get("alt_zh_cn", product.name_zh_cn),
                    sort_order=image.get("sort_order", 0),
                )
            )
    session.commit()


def _seed_shop_data_from_payload(session: Session, seed_data: dict[str, Any]) -> None:
    categories = _seed_categories_from_payload(session, seed_data)
    _seed_delivery_places_from_payload(session, seed_data)
    _seed_products_from_payload(session, seed_data, categories)


def _seed_categories(session: Session) -> dict[str, Category]:
    existing = session.exec(select(Category)).first()
    if existing:
        categories = session.exec(select(Category)).all()
        return {category.name_en: category for category in categories}

    categories = [
        Category(
            name_en="Groceries",
            name_ps="خوراکي توکي",
            name_zh_cn="食品杂货",
            sort_order=10,
        ),
        Category(
            name_en="Household",
            name_ps="د کور توکي",
            name_zh_cn="家居用品",
            sort_order=20,
        ),
        Category(
            name_en="Personal Care",
            name_ps="شخصي پاملرنه",
            name_zh_cn="个人护理",
            sort_order=30,
        ),
    ]
    for category in categories:
        session.add(category)
    session.commit()
    return {category.name_en: category for category in categories}


def _seed_delivery_places(session: Session) -> None:
    existing = session.exec(select(DeliveryPlace)).first()
    if existing:
        return

    places = [
        DeliveryPlace(
            name_en=f"Camp {number}",
            name_ps=f"کمپ {number}",
            name_zh_cn=f"{number}号营地",
            description_en=f"Delivery point for Camp {number}",
            description_ps=f"د کمپ {number} د سپارلو ځای",
            description_zh_cn=f"{number}号营地送货点",
            image_path=f"/media/delivery-places/camp-{number}.jpg",
            fee_afn=Decimal("80.00"),
            fee_cny=Decimal("6.00"),
            fee_usd=Decimal("1.00"),
            sort_order=number,
        )
        for number in range(1, 11)
    ]
    for place in places:
        session.add(place)
    session.commit()


def _seed_products(session: Session, categories: dict[str, Category]) -> None:
    existing = session.exec(select(Product)).first()
    if existing:
        return

    products = [
        Product(
            name_en="Sunflower Oil 1L",
            name_ps="د لمر ګل غوړي ۱ لیتر",
            name_zh_cn="葵花籽油1升",
            description_en="Cooking oil for daily use.",
            description_ps="د ورځني پخلي لپاره غوړي.",
            description_zh_cn="日常烹饪用油。",
            sku="OIL-1L",
            category_id=categories["Groceries"].id,
            stock_quantity=40,
            price_afn=Decimal("120.00"),
            price_cny=Decimal("10.00"),
            price_usd=Decimal("1.50"),
        ),
        Product(
            name_en="Biscuits Pack",
            name_ps="د بسکټو پاکټ",
            name_zh_cn="饼干包",
            description_en="Sweet biscuits for tea.",
            description_ps="د چای لپاره خوږ بسکټ.",
            description_zh_cn="配茶甜饼干。",
            sku="BISCUIT-01",
            category_id=categories["Groceries"].id,
            stock_quantity=80,
            price_afn=Decimal("60.00"),
            price_cny=Decimal("5.00"),
            price_usd=Decimal("0.80"),
        ),
        Product(
            name_en="Dishwashing Liquid",
            name_ps="د لوښو مينځلو مایع",
            name_zh_cn="洗洁精",
            description_en="Liquid soap for dishes.",
            description_ps="د لوښو لپاره مایع صابون.",
            description_zh_cn="餐具清洁液。",
            sku="DISH-LIQ",
            category_id=categories["Household"].id,
            stock_quantity=25,
            price_afn=Decimal("150.00"),
            price_cny=Decimal("12.00"),
            price_usd=Decimal("2.00"),
        ),
        Product(
            name_en="Shampoo",
            name_ps="شامپو",
            name_zh_cn="洗发水",
            description_en="Daily hair shampoo.",
            description_ps="د ورځني ویښتانو شامپو.",
            description_zh_cn="日常洗发水。",
            sku="SHAMPOO-01",
            category_id=categories["Personal Care"].id,
            stock_quantity=18,
            price_afn=Decimal("220.00"),
            price_cny=Decimal("18.00"),
            price_usd=Decimal("3.00"),
        ),
    ]
    for product in products:
        session.add(product)
        session.flush()
        session.add(
            ProductImage(
                product_id=product.id,
                image_path="/media/products/placeholder.jpg",
                alt_en=product.name_en,
                alt_ps=product.name_ps,
                alt_zh_cn=product.name_zh_cn,
            )
        )
    session.commit()


def seed_shop_data(session: Session) -> None:
    seed_data = _load_external_seed()
    if seed_data is not None:
        _seed_shop_data_from_payload(session, seed_data)
        return

    categories = _seed_categories(session)
    _seed_delivery_places(session)
    _seed_products(session, categories)


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        seed_shop_data(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
