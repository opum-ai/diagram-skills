import os

import stripe

stripe.api_key = os.environ.get("STRIPE_API_KEY", "")


class PaymentDeclined(Exception):
    pass


def charge(customer_id: int, amount_cents: int) -> str:
    """Charge the customer's saved card. Returns the PaymentIntent id."""
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents, currency="usd", customer=str(customer_id), confirm=True
        )
    except stripe.error.CardError as e:
        raise PaymentDeclined(str(e)) from e
    return intent.id
