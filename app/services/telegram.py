import logging

import httpx

from app.core.config import settings
from app.models import Order

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


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
            f"Currency: {_enum_value(order.currency)}",
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
        logger.info("Telegram notification skipped: settings are not configured")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_OWNER_CHAT_ID,
        "text": _format_order_message(order),
    }
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
        logger.info("Telegram order notification sent for %s", order.order_number)
    except httpx.HTTPStatusError as error:
        logger.warning(
            "Telegram order notification failed for %s with status %s",
            order.order_number,
            error.response.status_code,
        )
    except httpx.RequestError:
        logger.warning(
            "Telegram order notification failed for %s due to request error",
            order.order_number,
        )
