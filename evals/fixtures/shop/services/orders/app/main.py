from fastapi import FastAPI, HTTPException

from . import db, payments
from .states import OrderStatus, transition

app = FastAPI(title="orders-api")


@app.post("/orders", status_code=201)
def create_order(body: dict):
    order_id, total = db.insert_order(body["customer_id"], body["items"])  # status PLACED
    try:
        payments.charge(body["customer_id"], total)
    except payments.PaymentDeclined:
        db.set_status(order_id, transition(OrderStatus.PLACED, OrderStatus.PAYMENT_FAILED))
        raise HTTPException(status_code=402, detail="payment declined")
    db.set_status(order_id, transition(OrderStatus.PLACED, OrderStatus.PAID))
    return {"id": order_id, "status": OrderStatus.PAID.value}


@app.post("/orders/{order_id}/refund")
def refund_order(order_id: int):
    current = db.get_status(order_id)
    db.set_status(order_id, transition(current, OrderStatus.REFUNDED))
    return {"id": order_id, "status": OrderStatus.REFUNDED.value}
