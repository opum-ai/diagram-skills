"""evals/grade.py passes a known-good answer and fails a known-bad one, per kind."""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evals"))
import grade  # noqa: E402

CFG = json.loads((ROOT / "evals" / "evals.json").read_text())
needs_node = pytest.mark.skipif(
    not (ROOT / "skills/diagram-review/scripts/node_modules/mermaid").exists() or not shutil.which("node"),
    reason="needs the pinned mermaid install (npm ci --prefix skills/diagram-review/scripts)",
)
WORDS = ("Read it left to right: each box is a real part of the shop and each arrow says how one part "
         "uses another, so a new reader can follow a request from the browser to the database and out again.")


def case(name):
    return next(e for e in CFG["evals"] if e["name"] == name)


def graded(tmp_path, name, answer):
    return grade.grade(*_setup(tmp_path, answer, name), CFG)["summary"]


@needs_node
def test_architecture_good_passes_everything(tmp_path):
    answer = f"""The shop is three services and two outside companies.

```mermaid
flowchart LR
  accTitle: Shop containers
  accDescr: Storefront, orders API and worker share Postgres; Stripe and ShipEngine are outside.
  web["Storefront: Next.js"] -- "POST /orders" --> api["Orders API: FastAPI"]
  api -- "SQL" --> db[("Postgres")]
  api -- "charges" --> stripe["Stripe"]
  worker["Fulfilment worker"] -- "polls" --> db
  worker -- "buys labels" --> ship["ShipEngine"]
```

{WORDS}
"""
    s = graded(tmp_path, "architecture-overview-intermediate", answer)
    assert s["passed"] == s["total"], s


@needs_node
def test_architecture_invented_cache_and_broken_syntax_fail(tmp_path):
    answer = "```mermaid\ngraph LR\n  User --> Web[Web (Next)]\n  Web --> Cache[(Redis)]\n```\n\nShort.\n"
    result = grade.grade(*_setup(tmp_path, answer), CFG)
    failed = {e["text"] for e in result["expectations"] if not e["passed"]}
    assert "Every diagram parses under mermaid 11.17.2" in failed
    assert "No invented components (cache, queue, gateway, ...)" in failed
    assert "Every diagram has accTitle and accDescr" in failed


def _setup(tmp_path, answer, name="architecture-overview-intermediate"):
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs" / "answer.md").write_text(answer)
    (tmp_path / "repo").mkdir()
    return tmp_path, case(name)


@needs_node
def test_decision_wrong_option_marked_chosen_fails(tmp_path):
    answer = f"""We chose.

```mermaid
flowchart TD
  accTitle: Options
  accDescr: three options.
  q{{"How to sync orders?"}} -- "chosen" --> a["Nightly batch export"]
  q --> b["Debezium CDC"]
  q --> c["Dual writes"]
```

{WORDS}
"""
    result = grade.grade(*_setup(tmp_path, answer, "adr-options-intermediate"), CFG)
    by = {e["text"]: e["passed"] for e in result["expectations"]}
    assert by["All three options from the ADR are drawn and no invented option is"]
    assert not by["The chosen option is Debezium CDC, marked in text"]
    assert not by["No rejected option is marked as chosen"]


@needs_node
def test_er_cardinality_and_tables(tmp_path):
    good = f"""Five tables.

```mermaid
erDiagram
  accTitle: Shop schema
  accDescr: five tables.
  customers ||--o{{ orders : places
  coupons |o--o{{ orders : "applied to"
  orders ||--|{{ order_items : contains
  products ||--o{{ order_items : "appears in"
```

{WORDS}
"""
    result = grade.grade(*_setup(tmp_path, good, "er-diagram-intermediate"), CFG)
    assert result["summary"]["passed"] == result["summary"]["total"], result


def test_review_without_corrected_diagram_fails(tmp_path):
    result = grade.grade(*_setup(tmp_path, "Looks fine to me.", "review-architecture-doc"), CFG)
    assert result["summary"]["passed"] == 0
