import logging
from decimal import Decimal

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Category, DeliveryPlace, Product, ProductImage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
