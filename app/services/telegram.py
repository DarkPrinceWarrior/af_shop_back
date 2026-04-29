import httpx

from app.core.config import settings
from app.models import Order


def _format_order_message(order: Order) -> str:
    lines = [
        f"New order: {order.order_number}",
        f"Customer: {order.customer_name}",
        f"Phone: {order.customer_phone}",
    ]
    if order.customer_telegram:
        lines.append(f"Telegram: {order.customer_telegram}")
    lines.extend(
        [
            f"Currency: {order.currency.value}",
            f"Subtotal: {order.subtotal}",
            f"Delivery: {order.delivery_fee}",
            f"Total: {order.total}",
            "Items:",
        ]
    )
    for item in order.items:
        lines.append(
            f"- {item.product_name_en} x {item.quantity}: {item.line_total}"
        )
    if order.customer_comment:
        lines.append(f"Comment: {order.customer_comment}")
    return "\n".join(lines)


def send_order_notification(order: Order) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_OWNER_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_OWNER_CHAT_ID,
        "text": _format_order_message(order),
    }
    try:
        with httpx.Client(timeout=10) as client:
            client.post(url, json=payload).raise_for_status()
    except httpx.HTTPError:
        return
