# Shop architecture

This is how the shop fits together.

```mermaid
graph LR
  Customer --> Web[Storefront (Next.js)]
  Web --> Orders[Orders API]
  Orders --> Cache[(Redis cache)]
  Orders --> DB[(Postgres)]
  Orders --> Stripe
  Worker --> DB
```
