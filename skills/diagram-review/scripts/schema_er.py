#!/usr/bin/env python3
"""Draw SQL DDL as a Mermaid erDiagram, every entity traced to the file that defines it.

Reads CREATE TABLE statements (inline REFERENCES and table-level FOREIGN KEY),
ALTER TABLE ... ADD [CONSTRAINT x] FOREIGN KEY / ADD COLUMN, and DROP TABLE, in
file order, so a migrations directory replays to the current schema.

Cardinality is read from the schema, not guessed:
    child FK NOT NULL      -> every child row has exactly one parent  }o--||
    child FK nullable      -> a child row has zero or one parent      }o--o|
    child FK also UNIQUE   -> one-to-one                              |o--||

Usage: schema_er.py [--tables a,b] [--no-attributes] [--level L] [--title T] [--markdown] <file|dir>...
Exit codes: 0 ok, 2 nothing parsed, 3 more tables than the level's node cap.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_lint import NODE_CAPS  # noqa: E402

IDENT = r'[`"\[]?(?:\w+[`"\]]?\.)?[`"\[]?(\w+)[`"\]]?'


@dataclass
class Column:
    name: str
    type: str
    pk: bool = False
    unique: bool = False
    not_null: bool = False


@dataclass
class Table:
    name: str
    source: str
    columns: dict[str, Column] = field(default_factory=dict)
    fks: list[tuple[str, str, str]] = field(default_factory=list)  # (column, parent table, parent column)


def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    return re.sub(r"--[^\n]*", "", sql)


def split_top(body: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def statements(sql: str) -> list[str]:
    return [s.strip() for s in split_top_semicolons(strip_comments(sql)) if s.strip()]


def split_top_semicolons(sql: str) -> list[str]:
    out, depth, cur = [], 0, []
    for ch in sql:
        depth += ch == "("
        depth -= ch == ")"
        if ch == ";" and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def parse(files: list[Path], root: Path) -> dict[str, Table]:
    tables: dict[str, Table] = {}
    for f in files:
        rel = f.resolve().relative_to(root) if root in f.resolve().parents else f
        for st in statements(f.read_text(encoding="utf-8", errors="replace")):
            m = re.match(rf"create\s+table\s+(?:if\s+not\s+exists\s+)?{IDENT}\s*\((.*)\)\s*[^()]*$", st, re.I | re.S)
            if m:
                t = Table(m.group(1), f"{rel}#{m.group(1)}")
                for item in split_top(m.group(2)):
                    add_item(t, item)
                tables[t.name.lower()] = t
                continue
            m = re.match(rf"alter\s+table\s+(?:only\s+)?{IDENT}\s+(.*)$", st, re.I | re.S)
            if m and m.group(1).lower() in tables:
                t = tables[m.group(1).lower()]
                for action in split_top(m.group(2)):
                    a = re.sub(r"^add\s+(column\s+)?(constraint\s+\w+\s+)?", "", action.strip(), flags=re.I)
                    if a != action.strip():
                        add_item(t, a)
                continue
            m = re.match(rf"drop\s+table\s+(?:if\s+exists\s+)?{IDENT}", st, re.I)
            if m:
                tables.pop(m.group(1).lower(), None)
    return tables


def add_item(t: Table, item: str) -> None:
    low = item.lower()
    m = re.match(rf"(?:constraint\s+\w+\s+)?foreign\s+key\s*\(\s*{IDENT}\s*\)\s*references\s+{IDENT}\s*(?:\(\s*{IDENT}\s*\))?", item, re.I)
    if m:
        t.fks.append((m.group(1), m.group(2), m.group(3) or "id"))
        return
    m = re.match(rf"(?:constraint\s+\w+\s+)?primary\s+key\s*\((.*?)\)", item, re.I)
    if m:
        for c in re.findall(r"\w+", m.group(1)):
            if c in t.columns:
                t.columns[c].pk = True
        return
    m = re.match(rf"(?:constraint\s+\w+\s+)?unique\s*\((.*?)\)", item, re.I)
    if m:
        cols = re.findall(r"\w+", m.group(1))
        if len(cols) == 1 and cols[0] in t.columns:
            t.columns[cols[0]].unique = True
        return
    if re.match(r"(check|index|key|exclude)\b", low):
        return
    m = re.match(rf"{IDENT}\s+([\w ]+?(?:\([^)]*\))?(?:\[\])?)(?=\s|$)(.*)$", item, re.S)
    if not m:
        return
    name, typ, rest = m.group(1), m.group(2), m.group(3)
    col = Column(name, re.sub(r"\(.*\)|\W", "", typ.split()[0]) or "unknown",
                 pk=bool(re.search(r"primary\s+key", rest, re.I)),
                 unique=bool(re.search(r"\bunique\b", rest, re.I)),
                 not_null=bool(re.search(r"not\s+null|primary\s+key", rest, re.I)))
    t.columns[name] = col
    r = re.search(rf"references\s+{IDENT}\s*(?:\(\s*{IDENT}\s*\))?", rest, re.I)
    if r:
        t.fks.append((name, r.group(1), r.group(2) or "id"))


def render(tables: dict[str, Table], title: str, level: str, attributes: bool) -> tuple[str, str]:
    names = {k: t.name for k, t in tables.items()}
    rels = []
    for t in tables.values():
        for col, parent, pcol in t.fks:
            if parent.lower() not in tables:
                continue
            c = t.columns.get(col)
            one_to_one = c is not None and (c.unique or (c.pk and len([x for x in t.columns.values() if x.pk]) == 1))
            left = "|o" if one_to_one else "}o"
            right = "||" if (c is None or c.not_null) else "o|"
            rels.append(f'  {t.name} {left}--{right} {names[parent.lower()]} : "{col}"')
    lines = [
        "erDiagram",
        f"  accTitle: {title}",
        f"  accDescr: {len(tables)} tables and the {len(rels)} foreign keys between them, read from the schema files. Each line runs from the table holding the foreign key to the table it points at.",
        f"  %% level: {level}",
        "  %% generated by schema_er.py from the DDL; regenerate rather than hand-edit",
    ]
    for t in tables.values():
        if attributes and t.columns:
            lines.append(f"  {t.name} {{")
            fkcols = {c for c, _, _ in t.fks}
            for c in t.columns.values():
                keys = ",".join(k for k, on in (("PK", c.pk), ("FK", c.name in fkcols), ("UK", c.unique and not c.pk)) if on)
                lines.append(f"    {c.type} {c.name}{' ' + keys if keys else ''}")
            lines.append("  }")
        else:
            lines.append(f"  {t.name}")
    lines += rels
    lines += [f"  %% ref {t.name} = schema:{t.source}" for t in tables.values()]
    key = ("Key: `||` exactly one, `o|` zero or one, `}o` zero or more; "
           "PK primary key, FK foreign key, UK unique.")
    return "\n".join(lines) + "\n", key


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--root", default=".")
    ap.add_argument("--tables", help="comma-separated tables to keep")
    ap.add_argument("--no-attributes", action="store_true", help="entities only (beginner views)")
    ap.add_argument("--level", choices=sorted(NODE_CAPS), default="intermediate")
    ap.add_argument("--title", default="Data model")
    ap.add_argument("--markdown", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    files: list[Path] = []
    for p in map(Path, a.paths):
        files += sorted(p.rglob("*.sql")) if p.is_dir() else [p]
    tables = parse(files, root)
    if a.tables:
        keep = {s.strip().lower() for s in a.tables.split(",")}
        tables = {k: v for k, v in tables.items() if k in keep}
    if not tables:
        print("no CREATE TABLE statements found", file=sys.stderr)
        return 2
    cap = NODE_CAPS[a.level]
    if len(tables) > cap:
        print(f"{len(tables)} tables exceed the {a.level} cap of {cap}; pick one area with --tables", file=sys.stderr)
        return 3
    mermaid, key = render(tables, a.title, a.level, not a.no_attributes)
    if a.markdown:
        print(f"```mermaid\n{mermaid}```\n\n{key}")
    else:
        print(mermaid, end="")
        print(key, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
