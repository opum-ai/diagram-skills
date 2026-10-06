"""repo_inventory.py reports only what the repository shows."""
import json
from pathlib import Path

import repo_inventory as ri

ROOT = Path(__file__).resolve().parent.parent
SHOP = ROOT / "evals" / "fixtures" / "shop"


# ---- repo_inventory

def test_repo_inventory_finds_real_units_and_datastores(capsys):
    assert ri.main(["--root", str(SHOP)]) == 0
    inv = json.loads(capsys.readouterr().out)
    names = {u["name"] for u in inv["units"]}
    assert {"shop-web", "orders-api", "fulfilment-worker"} <= names
    assert [d["name"] for d in inv["datastores"]] == ["postgres"]
    assert "Stripe" in [e["name"] for e in inv["externals"]]
    assert all("redis" not in json.dumps(d).lower() for d in inv["datastores"])
