// The storefront talks to the orders API over HTTP; it never touches the database.
const ORDERS_URL = process.env.ORDERS_URL ?? "http://localhost:8000";

export async function placeOrder(customerId: number, items: { productId: number; qty: number }[]) {
  const res = await fetch(`${ORDERS_URL}/orders`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ customer_id: customerId, items }),
  });
  if (res.status === 402) throw new Error("Payment declined");
  if (!res.ok) throw new Error(`Order failed: ${res.status}`);
  return res.json();
}
