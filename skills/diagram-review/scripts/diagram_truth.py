#!/usr/bin/env python3
"""Check that every node in a Mermaid diagram traces to a real source of truth.

The parse check proves a diagram renders; this proves it is not invented.
Each node names its source in a Mermaid comment line, which renderers ignore:

    %% ref api      = path:services/api
    %% ref handler  = path:src/orders.py#place_order
    %% ref DSKI-3   = quest:DSKI-3
    %% ref adr1     = lore:adr/0001-use-mermaid-in-markdown-as-the-diagram-notation
    %% ref orders   = schema:db/migrations/001_init.sql#orders
    %% ref users    = ext:Engineers who read the docs

Ref kinds and how each resolves (relative to --root):
    path:   the file or directory exists; with #symbol, the symbol appears in it
    schema: the file exists and defines the object (CREATE TABLE, model, class)
    quest:  `quest task|decision|milestone view <id>` succeeds
    lore:   docs/<id>.md exists in the bundle
    ext:    an external actor or system; never fails, but is listed as asserted

A fence may also declare `%% edges: quest-dependencies`. Then every edge
between two quest nodes must match Quest's `dependencies` exactly
(prerequisite --> dependent), and every dependency between drawn nodes must
be drawn.

Usage: diagram_truth.py [--root DIR] [--quest-snapshot FILE]... [--json] <file|dir>...
Exit codes: 0 every node traced, 1 at least one untraced or unresolved node, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagram_lint as dl  # noqa: E402
from diagram_lint import flow_edges  # noqa: E402

REF_RE = re.compile(r"^\s*%%\s*ref\s+(\S+)\s*=\s*(path|schema|quest|lore|ext):\s*(.+?)\s*$", re.M)
EDGES_RE = re.compile(r"^\s*%%\s*edges:\s*quest-dependencies\s*$", re.M)


@dataclass
class Finding:
    where: str
    node: str
    rule: str
    severity: str
    message: str


# ---------------------------------------------------------------- resolvers

def _inside(root: Path, rel: str) -> Path | None:
    p = (root / rel).resolve()
    return p if p == root or root in p.parents else None


def _text_of(p: Path) -> str:
    if p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return "\n".join(
        q.read_text(encoding="utf-8", errors="replace")
        for q in sorted(p.rglob("*"))
        if q.is_file() and q.stat().st_size < 1_000_000 and ".git" not in q.parts and "node_modules" not in q.parts
    )


def resolve_path(root: Path, target: str) -> str | None:
    rel, _, symbol = target.partition("#")
    p = _inside(root, rel)
    if p is None or not p.exists():
        return f"path `{rel}` does not exist"
    if symbol and not re.search(rf"\b{re.escape(symbol)}\b", _text_of(p)):
        return f"`{symbol}` does not appear in `{rel}`"
    return None


def resolve_schema(root: Path, target: str) -> str | None:
    rel, _, obj = target.partition("#")
    p = _inside(root, rel)
    if p is None or not p.exists():
        return f"schema file `{rel}` does not exist"
    if not obj:
        return "schema ref needs `#<table or model>`"
    pat = rf"(create\s+table\s+(if\s+not\s+exists\s+)?[`\"\[]?(\w+\.)?{re.escape(obj)}\b|\bmodel\s+{re.escape(obj)}\b|\bclass\s+{re.escape(obj)}\b|\btype\s+{re.escape(obj)}\b|\binterface\s+{re.escape(obj)}\b)"
    if not re.search(pat, _text_of(p), re.I):
        return f"`{obj}` is not defined in `{rel}`"
    return None


# Saved `quest task|decision|milestone list --json` envelopes, keyed by id. When set,
# lookups read these instead of calling quest (tests, evals, CI without a tracker).
SNAPSHOT: dict[str, dict] = {}


def load_snapshot(paths: list[str]) -> None:
    for path in paths:
        doc = json.loads(Path(path).read_text())
        for rec in doc["data"] if isinstance(doc, dict) else doc:
            SNAPSHOT[rec["id"]] = rec


@lru_cache(maxsize=None)
def _quest(root: str, kind: str, ident: str) -> dict | None:
    if SNAPSHOT:
        return SNAPSHOT.get(ident)
    try:
        r = subprocess.run(["quest", kind, "view", ident, "--json"], cwd=root, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout).get("data")
    except json.JSONDecodeError:
        return None


def quest_kind(ident: str) -> str:
    if ident.upper().startswith("DEC-"):
        return "decision"
    if re.match(r"^M-\d+$", ident, re.I):
        return "milestone"
    return "task"


def resolve_quest(root: Path, target: str) -> str | None:
    ident = target.strip()
    if _quest(str(root), quest_kind(ident), ident) is None:
        return f"Quest has no {quest_kind(ident)} `{ident}`"
    return None


def resolve_lore(root: Path, target: str) -> str | None:
    cid = target.strip().removesuffix(".md")
    if not (root / "docs" / f"{cid}.md").is_file():
        return f"lore doc `{cid}` does not exist under docs/"
    return None


RESOLVERS = {"path": resolve_path, "schema": resolve_schema, "quest": resolve_quest, "lore": resolve_lore}


# ---------------------------------------------------------------- edges

def check_quest_edges(d: dl.Diagram, root: Path, refs: dict[str, tuple[str, str]]) -> list[Finding]:
    out = []
    qnodes = {node: target.strip() for node, (kind, target) in refs.items() if kind == "quest"}
    by_id = {v: k for k, v in qnodes.items()}
    expected = set()
    for node, ident in qnodes.items():
        data = _quest(str(root), "task", ident) or {}
        for dep in data.get("dependencies", []) or []:
            if dep in by_id:
                expected.add((by_id[dep], node))
    drawn = {e for e in flow_edges(d.src) if e[0] in qnodes and e[1] in qnodes}
    for a, b in sorted(drawn - expected):
        out.append(Finding(d.where, f"{a}->{b}", "edge-not-in-source", "error", f"`{qnodes[a]}` --> `{qnodes[b]}` is drawn but Quest has no such dependency"))
    for a, b in sorted(expected - drawn):
        out.append(Finding(d.where, f"{a}->{b}", "edge-missing", "error", f"Quest says `{qnodes[b]}` depends on `{qnodes[a]}`, but the edge is not drawn"))
    return out


# ---------------------------------------------------------------- main check

def check(d: dl.Diagram, root: Path) -> list[Finding]:
    out: list[Finding] = []
    refs = {m.group(1): (m.group(2), m.group(3)) for m in REF_RE.finditer(d.src)}
    nodes = dl.nodes_of(d.src)
    for node in sorted(nodes):
        if node not in refs:
            out.append(Finding(d.where, node, "untraced", "error", f"node `{node}` has no `%% ref {node} = <kind>:<target>` line"))
            continue
        kind, target = refs[node]
        if kind == "ext":
            out.append(Finding(d.where, node, "external", "info", f"asserted external: {target}"))
            continue
        problem = RESOLVERS[kind](root, target)
        if problem:
            out.append(Finding(d.where, node, "unresolved", "error", problem))
    for node in sorted(set(refs) - nodes):
        out.append(Finding(d.where, node, "orphan-ref", "warning", f"`%% ref {node}` names no node in the diagram"))
    if EDGES_RE.search(d.src):
        out.extend(check_quest_edges(d, root, refs))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--root", default=".", help="repository root that refs resolve against")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quest-snapshot", action="append", default=[], metavar="FILE",
                    help="saved `quest ... list --json` output to resolve quest refs against (repeatable)")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    SNAPSHOT.clear()
    _quest.cache_clear()
    load_snapshot(a.quest_snapshot)
    findings: list[Finding] = []
    count = 0
    for target in a.paths:
        p = Path(target)
        if not p.exists():
            print(f"no such path: {p}", file=sys.stderr)
            return 2
        for file in dl.walk(p):
            for d in dl.diagrams_in(file):
                count += 1
                findings.extend(check(d, root))
    errors = sum(1 for x in findings if x.severity == "error")
    if a.json:
        print(json.dumps({"diagrams": count, "errors": errors, "findings": [asdict(x) for x in findings]}, indent=2))
    else:
        for x in findings:
            print(f"{x.severity.upper():7} {x.where} [{x.rule}] {x.node}: {x.message}")
        print(f"\n{count} diagrams, {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
