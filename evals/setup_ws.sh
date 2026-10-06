#!/usr/bin/env bash
# Build a fresh eval workspace: a copy of the shop fixture as its own git
# repository, with a Quest tracker created through the quest CLI (never by
# hand), and the review fixtures' broken docs when the case asks for them.
#
# Usage: evals/setup_ws.sh <dest-dir> [--with-review-docs]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="$1"; shift || true
review=0; [ "${1:-}" = "--with-review-docs" ] && review=1
rm -rf "$dest"; mkdir -p "$dest"
cp -R "$here/fixtures/shop/." "$dest/"
[ $review -eq 1 ] && cp -R "$here/fixtures/review-docs/docs/." "$dest/docs/"
cd "$dest"
git init -q && git config user.name fixture && git config user.email fixture@example.com
git add -A && git commit -qm "shop fixture"

A=(--actor fixture --actor-kind human --json)
quest init --name Shop --task-id-prefix SHOP --skill-source none >/dev/null
mk() { quest task create "$@" "${A[@]}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["id"])'; }
quest milestone create "Public launch" "${A[@]}" >/dev/null                      # M-1
P=$(mk "Payments" --type feature)                                                # SHOP-1 (epic)
S2=$(mk "Stripe account and API keys" --parent "$P")
S3=$(mk "Charge the card when an order is placed" --parent "$P" --dependency "$S2")
S4=$(mk "Handle declined cards" --parent "$P" --dependency "$S3" --milestone M-1)
S5=$(mk "Refund endpoint" --parent "$P" --dependency "$S3" --milestone M-1)
S6=$(mk "Buy shipping labels from ShipEngine" --milestone M-1)
S7=$(mk "Fulfilment worker polls paid orders" --dependency "$S6" --milestone M-1)
S8=$(mk "Order confirmation emails" --dependency "$S3" --milestone M-1)
S9=$(mk "Load test checkout" --dependency "$S4" --dependency "$S7" --milestone M-1)
S10=$(mk "Launch checklist sign-off" --dependency "$S9" --dependency "$S5" --dependency "$S8" --milestone M-1)
for t in "$S2" "$S3"; do
  quest task edit "$t" --status "In Progress" "${A[@]}" >/dev/null
  quest task complete "$t" "${A[@]}" >/dev/null
done
for t in "$P" "$S4"; do quest task edit "$t" --status "In Progress" "${A[@]}" >/dev/null; done
quest decision create "Sync orders to the analytics warehouse" --status accepted \
  --context "Options: nightly batch export; change data capture with Debezium; dual writes from the orders API. See docs/adr/0003-sync-orders-to-the-analytics-warehouse.md" \
  --outcome "Change data capture with Debezium" "${A[@]}" >/dev/null           # DEC-1
git add -A && git commit -qm "tracker" && echo "workspace ready: $dest"
