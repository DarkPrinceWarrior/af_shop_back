# Frontend API Guide

Base URL in local Docker:

```text
http://localhost:8000
```

API prefix:

```text
/api/v1
```

## Public Shop API

### Bootstrap catalog

Use this as the first request for the customer storefront.

```http
GET /api/v1/catalog/bootstrap?language=en&currency=AFN
```

Supported languages:

- `en`
- `ps`
- `zh-CN`

Supported currencies:

- `AFN`
- `CNY`
- `USD`

Response includes:

- selected language and currency;
- all supported languages and currencies;
- active categories with localized `name`;
- active products with localized `name`, localized `description`, selected-currency `price`, stock, images;
- active delivery places with localized `name`, localized `description`, selected-currency `delivery_fee`, image.

### Catalog views

These endpoints return frontend-ready localized objects:

```http
GET /api/v1/catalog/categories/view?language=en
GET /api/v1/catalog/products/view?language=zh-CN&currency=CNY
GET /api/v1/catalog/delivery-places/view?language=ps&currency=AFN
```

Product filters:

```http
GET /api/v1/catalog/products/view?category_id=<uuid>&q=oil&language=en&currency=USD
```

### Raw catalog data

These endpoints return full multilingual/admin-like objects:

```http
GET /api/v1/catalog/categories
GET /api/v1/catalog/products
GET /api/v1/catalog/delivery-places
```

### Quote order

Use before final submit to show subtotal, delivery fee, total, and item lines without reducing stock.

```http
POST /api/v1/catalog/orders/quote
Content-Type: application/json
```

```json
{
  "customer_name": "Ali",
  "customer_phone": "+93000000000",
  "customer_telegram": "@ali",
  "customer_comment": "Call before delivery",
  "language": "en",
  "currency": "AFN",
  "delivery_place_id": "delivery-place-uuid",
  "items": [
    {
      "product_id": "product-uuid",
      "quantity": 2
    }
  ]
}
```

### Create order

Creates the order, validates stock, reduces stock, stores the order, broadcasts the admin WebSocket event, and sends Telegram notification when configured.

```http
POST /api/v1/catalog/orders
Content-Type: application/json
```

Payload is the same as quote.

Important responses:

- `200`: order created;
- `404`: product or delivery place not found/inactive;
- `409`: not enough stock.

## Admin Auth

Login:

```http
POST /api/v1/login/access-token
Content-Type: application/x-www-form-urlencoded
```

Form fields:

```text
username=admin@example.com
password=changethis
```

Use the returned access token:

```http
Authorization: Bearer <token>
```

## Admin API

### Dashboard

```http
GET /api/v1/admin/dashboard
Authorization: Bearer <token>
```

Returns product counts, delivery-place counts, new orders, and active orders.

### Orders

List:

```http
GET /api/v1/admin/orders?skip=0&limit=100
Authorization: Bearer <token>
```

Supported query parameters:

- `skip`: pagination offset, default `0`;
- `limit`: page size from `1` to `100`, default `100`;
- `status`: `new`, `accepted`, `preparing`, `delivering`, `completed`, `cancelled`;
- `q`: search by order number, customer name, phone, or Telegram;
- `date_from`: include orders created from this date, format `YYYY-MM-DD`;
- `date_to`: include orders created through this date, format `YYYY-MM-DD`.

Orders are sorted newest first.

Example:

```http
GET /api/v1/admin/orders?status=accepted&q=%4093700000000&date_from=2026-04-01&date_to=2026-04-30
Authorization: Bearer <token>
```

Detail:

```http
GET /api/v1/admin/orders/{order_id}
Authorization: Bearer <token>
```

Update status:

```http
PATCH /api/v1/admin/orders/{order_id}/status
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "status": "accepted",
  "admin_comment": "Confirmed by phone"
}
```

Supported statuses:

- `new`
- `accepted`
- `preparing`
- `delivering`
- `completed`
- `cancelled`

Cancel order and return stock once:

```http
POST /api/v1/admin/orders/{order_id}/cancel
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "admin_comment": "Customer cancelled"
}
```

Complete order:

```http
POST /api/v1/admin/orders/{order_id}/complete
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "admin_comment": "Delivered and paid"
}
```

Update only admin comment:

```http
PATCH /api/v1/admin/orders/{order_id}/comment
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "admin_comment": "Customer prefers evening delivery"
}
```

Order detail includes `status_history`, `admin_comment`, and `stock_returned_at`.

### Real-time orders

Connect with token as query parameter:

```text
ws://localhost:8000/api/v1/admin/orders/ws?token=<token>
```

New order event:

```json
{
  "type": "order.created",
  "order_id": "order-uuid",
  "order_number": "SM-20260429214230-822B5F",
  "total": "21.00",
  "currency": "CNY"
}
```

### Products

```http
GET /api/v1/admin/products
POST /api/v1/admin/products
PATCH /api/v1/admin/products/{product_id}
DELETE /api/v1/admin/products/{product_id}
POST /api/v1/admin/products/{product_id}/images
```

### Categories

```http
GET /api/v1/admin/categories
POST /api/v1/admin/categories
PATCH /api/v1/admin/categories/{category_id}
DELETE /api/v1/admin/categories/{category_id}
```

### Delivery places

```http
GET /api/v1/admin/delivery-places
POST /api/v1/admin/delivery-places
PATCH /api/v1/admin/delivery-places/{place_id}
DELETE /api/v1/admin/delivery-places/{place_id}
```

### Media upload

```http
POST /api/v1/admin/media/images
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

Form field:

```text
file=<image>
```

Returns:

```json
{
  "image_path": "/media/images/<file>.jpg"
}
```
