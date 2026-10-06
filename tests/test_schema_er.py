"""schema_er.py reads cardinality from DDL and traces every table."""
from pathlib import Path

import diagram_lint as dl
import diagram_truth as dt
import schema_er as se

ROOT = Path(__file__).resolve().parent.parent
SHOP = ROOT / "evals" / "fixtures" / "shop"


def lint_ok(mermaid):
    return [f for f in dl.lint(dl.Diagram(where="x", src=mermaid), "intermediate") if f.severity == "error"]


# ---- schema_er

def test_schema_er_reads_cardinality_and_replays_drops(capsys):
    assert se.main(["--root", str(SHOP), str(SHOP / "db" / "migrations")]) == 0
    out = capsys.readouterr().out
    assert "legacy_carts" not in out
    assert "orders }o--|| customers" in out and "orders }o--o| coupons" in out
    assert "%% ref coupons = schema:db/migrations/002_coupons.sql#coupons" in out
    assert lint_ok(out) == []


def test_schema_er_output_traces(tmp_path, capsys):
    se.main(["--root", str(SHOP), "--markdown", str(SHOP / "db" / "migrations")])
    md = tmp_path / "er.md"
    md.write_text("Data?\n\n" + capsys.readouterr().out + "\nWords " * 25)
    assert dt.main(["--root", str(SHOP), "--json", str(md)]) == 0
