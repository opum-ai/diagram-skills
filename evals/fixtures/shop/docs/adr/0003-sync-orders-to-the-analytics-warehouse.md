# ADR-0003: Sync orders to the analytics warehouse with change data capture

## Status

Accepted (2026-09-12). Mirrors Quest decision DEC-1.

## Context

Finance wants order data in the analytics warehouse within minutes, not
days. Three options were considered:

1. **Nightly batch export.** A cron job dumps the `orders` table to the
   warehouse every night. Simple, but data is up to 24 hours stale.
2. **Change data capture with Debezium.** Debezium reads Postgres's
   write-ahead log and streams every change to the warehouse. Fresh within
   a minute, and no change to application code, but it adds a Debezium
   connector to run and monitor.
3. **Dual writes from the orders API.** The API writes each order to
   Postgres and to the warehouse. Fresh, but the two writes can disagree
   when one fails, and every new write path must remember to do both.

## Decision

We will use change data capture with Debezium (option 2).

## Consequences

- Finance sees orders within about a minute.
- Operations owns one more component, the Debezium connector, and its lag
  alert.
- The orders API stays unaware of analytics.
