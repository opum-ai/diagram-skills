"""Polls Postgres for paid orders, buys a shipping label from ShipEngine,
and marks the order shipped."""
import os
import time

import httpx
import psycopg

SHIPENGINE = "https://api.shipengine.com/v1/labels"


def ship_paid_orders(conn) -> None:
    for (order_id,) in conn.execute("SELECT id FROM orders WHERE status = 'paid'").fetchall():
        httpx.post(SHIPENGINE, headers={"API-Key": os.environ["SHIPENGINE_API_KEY"]}, json={"order": order_id})
        conn.execute("UPDATE orders SET status = 'shipped' WHERE id = %s", (order_id,))


if __name__ == "__main__":
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        while True:
            ship_paid_orders(conn)
            time.sleep(30)
