import os

import psycopg

DSN = os.environ["DATABASE_URL"]


def insert_order(customer_id: int, items: list) -> tuple[int, int]:
    with psycopg.connect(DSN) as conn:
        total = sum(conn.execute("SELECT 100 * qty").fetchone()[0] for _ in items)
        row = conn.execute(
            "INSERT INTO orders (customer_id, total) VALUES (%s, %s) RETURNING id", (customer_id, total / 100)
        ).fetchone()
        return row[0], total


def set_status(order_id: int, status) -> None:
    with psycopg.connect(DSN) as conn:
        conn.execute("UPDATE orders SET status = %s WHERE id = %s", (status.value, order_id))


def get_status(order_id: int):
    from .states import OrderStatus
    with psycopg.connect(DSN) as conn:
        return OrderStatus(conn.execute("SELECT status FROM orders WHERE id = %s", (order_id,)).fetchone()[0])
