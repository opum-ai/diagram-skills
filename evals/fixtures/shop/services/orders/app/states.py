"""Order lifecycle. Every status change goes through `transition`, which
rejects any move not listed in ALLOWED."""
from enum import Enum


class OrderStatus(str, Enum):
    PLACED = "placed"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"
    SHIPPED = "shipped"
    REFUNDED = "refunded"


ALLOWED = {
    OrderStatus.PLACED: {OrderStatus.PAID, OrderStatus.PAYMENT_FAILED},
    OrderStatus.PAYMENT_FAILED: {OrderStatus.PAID},  # customer retries with another card
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.REFUNDED},
    OrderStatus.SHIPPED: set(),
    OrderStatus.REFUNDED: set(),
}


class IllegalTransition(Exception):
    pass


def transition(current: OrderStatus, target: OrderStatus) -> OrderStatus:
    if target not in ALLOWED[current]:
        raise IllegalTransition(f"{current.value} -> {target.value}")
    return target
