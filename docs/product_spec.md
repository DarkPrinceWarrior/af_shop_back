# Shop Meraj Product Spec

## Goal

Build a simple online shop for local customers who need to order goods for delivery. The main priority is a fast order flow: customers should find products, choose a delivery place visually, and submit an order without creating an account.

The owner must see new orders in the admin panel in real time and also receive a Telegram notification.

## Languages

Default language: English.

Additional customer languages:

- Pashto
- Simplified Chinese

All customer-facing product names, category names, delivery-place names, and core UI labels should support these three languages.

## Currency And Payment

Supported currencies:

- AFN - Afghan afghani
- CNY - Chinese yuan
- USD - United States dollar

Payment method:

- Cash/payment on delivery only for the first version.

Prices are visible to all customers.

## Customer Flow

1. Customer opens the shop.
2. Customer selects interface language.
3. Customer browses catalog or searches products.
4. Customer adds products to cart.
5. Customer opens checkout.
6. Customer enters contact details.
7. Customer selects delivery place from photos.
8. Customer sees delivery fee and total amount.
9. Customer submits the order.
10. Customer receives order confirmation with order number/status.

No customer account is required.

## Catalog

The catalog should include:

- product categories;
- product search;
- product cards with image, localized name, price, available stock, and add-to-cart action;
- product details page if needed later.

Products should be managed from the admin panel. Manual admin entry is the best first approach because the assortment can change and there is no confirmed import source yet. Later, CSV/Excel import can be added if there are many products.

## Stock

Inventory tracking is required.

Each product should have:

- current stock quantity;
- active/inactive status;
- visible prices in AFN, CNY, and USD;
- optional low-stock threshold later.

Customers should not be able to order more than the available quantity.

## Delivery Places

Delivery is paid.

Customers should not have to type a full address. Instead, the admin creates about 10 predefined delivery places.

Each delivery place should have:

- photo;
- localized name in English, Pashto, and Simplified Chinese;
- optional localized description;
- delivery fees in AFN, CNY, and USD;
- active/inactive status;
- sort order.

At checkout, the customer selects the delivery place by photo.

## Orders

Order should contain:

- order number;
- customer name or short identifier;
- customer phone;
- customer Telegram contact;
- selected language;
- selected currency;
- selected delivery place;
- delivery fee;
- product items;
- item quantities;
- item prices at the moment of order;
- subtotal;
- total;
- customer comment;
- status;
- creation time.

Initial statuses:

- new;
- accepted;
- preparing;
- delivering;
- completed;
- cancelled.

## Admin Panel

Admin panel should include:

- login for owner/staff;
- real-time new order list;
- order details;
- order status update;
- product management;
- category management;
- stock management;
- delivery place management with photo upload;
- Telegram notification settings.

## Notifications

Required notification channels:

- real-time admin panel notification;
- Telegram message directly to the owner.

Telegram notification should include:

- order number;
- customer phone;
- customer Telegram contact;
- product list and quantities;
- subtotal;
- delivery fee;
- total;
- currency;
- selected delivery place name;
- delivery place photo or link to photo if practical;
- customer comment.

## Backend Scope

Backend stack:

- FastAPI;
- PostgreSQL;
- SQLModel;
- Alembic migrations;
- JWT auth for admin users;
- WebSocket or Server-Sent Events for real-time admin orders;
- Telegram Bot API integration for order notifications.

Core backend entities:

- AdminUser;
- Category;
- Product;
- ProductImage;
- DeliveryPlace;
- Order;
- OrderItem;
- TelegramSettings or notification config.

## First Version Priorities

1. Product/category data model.
2. Delivery places with photos and delivery fees.
3. Public catalog and search.
4. Cart-compatible order creation API.
5. Stock validation on order creation.
6. Admin order list and status updates.
7. Telegram notification on new order.
8. Real-time admin notification.

## Open Decisions

- Exact admin UI technology is not selected yet.
- Telegram recipient is the owner's private chat.
- Product image storage should start as local filesystem storage, then move to object storage if needed.
- Currency conversion is not required. Product prices and delivery fees should be managed manually per currency.
