# Order flow

The statuses an order moves through.

```mermaid
flowchart LR
  placed[Placed] --> paid[Paid (card charged)]
  placed --> failed[Payment failed]
  failed --> paid
  paid --> shipped[Shipped]
  paid --> refunded[Refunded]
  shipped --> end
  refunded --> end
```

Orders start as placed and end as shipped or refunded.
