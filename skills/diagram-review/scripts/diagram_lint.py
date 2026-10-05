#!/usr/bin/env python3
"""Lint Mermaid diagrams against the diagram-skills profile and level rules.

The parse check (mermaid-check.mjs) answers "does it render". This answers
"is it the kind of diagram the suite promises": accessible, inside the
conservative syntax profile, small enough for its reader, and explained.

Usage:
    diagram_lint.py [--level beginner|intermediate|advanced] [--json] <file|dir>...

A fence can set its own level with a comment line:  %% level: beginner
Exit codes: 0 no errors (warnings allowed), 1 at least one error, 2 usage.
Standard library only, like the sibling engines.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

NODE_CAPS = {"beginner": 7, "intermediate": 12, "advanced": 20}
DEFAULT_LEVEL = "intermediate"
MIN_EXPLANATION_WORDS = 20

# Types inside the conservative profile (ADR-0001), keyed by their header word.
PROFILE_TYPES = {
    "flowchart": "flowchart",
    "sequenceDiagram": "sequence",
    "stateDiagram-v2": "state",
    "erDiagram": "er",
    "classDiagram": "class",
    "gantt": "gantt",
    "C4Context": "c4",
}
# Types that parse but sit outside the profile, with the fix to suggest.
OFF_PROFILE = {
    "graph": "use `flowchart`; `graph` is the legacy keyword and renders differently",
    "stateDiagram": "use `stateDiagram-v2`",
}

FENCE_RE = re.compile(
    r"^([ \t]*)(`{3,}|~{3,})[ \t]*mermaid(?:[ \t][^\n]*)?\n(.*?)^\1\2[ \t]*$",
    re.M | re.S,
)
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
ARROW_RE = re.compile(r"\s*(?:<?(?:-{2,}|={2,}|-\.+-?)(?:>|o|x)?|~~~|&)\s*")


@dataclass
class Finding:
    where: str
    rule: str
    severity: str  # "error" | "warning"
    message: str


@dataclass
class Diagram:
    where: str
    src: str
    before: str = ""  # prose before the fence, back to the previous heading or fence
    after: str = ""  # prose after the fence, up to the next heading or fence
    in_markdown: bool = False


# ---------------------------------------------------------------- extraction

def diagrams_in(path: Path) -> list[Diagram]:
    text = path.read_text(encoding="utf-8")
    if path.suffix not in (".md", ".markdown"):
        return [Diagram(where=str(path), src=text)]
    out: list[Diagram] = []
    matches = list(FENCE_RE.finditer(text))
    for m in matches:
        line = text.count("\n", 0, m.start()) + 1
        out.append(
            Diagram(
                where=f"{path}:{line}",
                src=m.group(3),
                before=_prose_before(text, m.start()),
                after=_prose_after(text, m.end()),
                in_markdown=True,
            )
        )
    return out


def _prose_lines(lines: list[str]) -> list[str]:
    kept = []
    for ln in lines:
        if HEADING_RE.match(ln) or re.match(r"^\s*(`{3,}|~{3,})", ln):
            break
        kept.append(ln)
    return kept


def _prose_before(text: str, start: int) -> str:
    lines = text[:start].splitlines()
    return "\n".join(reversed(_prose_lines(list(reversed(lines)))))


def _prose_after(text: str, end: int) -> str:
    return "\n".join(_prose_lines(text[end:].splitlines()[1:]))


# ---------------------------------------------------------------- analysis

def _body_lines(src: str) -> list[tuple[int, str]]:
    """Diagram lines without comments, accessibility fields or blank lines."""
    out, in_block = [], False
    for i, raw in enumerate(src.splitlines(), start=1):
        s = raw.strip()
        if in_block:
            if s.startswith("}"):
                in_block = False
            continue
        if not s or s.startswith("%%"):
            continue
        if re.match(r"accDescr\s*\{", s):
            in_block = "}" not in s
            continue
        if re.match(r"acc(Title|Descr)\s*:", s):
            continue
        out.append((i, s))
    return out


def header(src: str) -> str:
    for _, s in _body_lines(src):
        return s.split()[0]
    return ""


def _strip_flow_line(s: str) -> str:
    s = re.sub(r'"[^"]*"', '""', s)  # quoted text
    s = re.sub(r"\|[^|]*\|", "", s)  # |edge label|
    s = re.sub(r'(--|==|-\.)\s*""\s*(-->|==>|\.->|---|-\.-|--x|--o)', r" \2 ", s)
    prev = None
    while prev != s:  # node shapes, innermost first
        prev = s
        s = re.sub(r"\([^()]*\)|\[[^\[\]]*\]|\{[^{}]*\}", "", s)
    s = re.sub(r">[^\s]*\]", "", s)  # asymmetric >label]
    return re.sub(r":::[\w-]+", "", s)


FLOW_SKIP = re.compile(r"^(flowchart|graph|classDef|class|style|linkStyle|click|direction|end)\b")


def flow_nodes(src: str) -> tuple[set[str], set[str]]:
    nodes: set[str] = set()
    subgraphs: set[str] = set()
    for _, s in _body_lines(src):
        m = re.match(r"subgraph\s+([\w-]+)", s)
        if m:
            subgraphs.add(m.group(1))
            continue
        if FLOW_SKIP.match(s):
            continue
        for part in ARROW_RE.split(_strip_flow_line(s)):
            part = part.strip().strip(";")
            if re.fullmatch(r"[A-Za-z0-9_][\w-]*", part):
                nodes.add(part)
    return nodes - subgraphs, subgraphs


def sequence_nodes(src: str) -> set[str]:
    nodes = set()
    for _, s in _body_lines(src):
        m = re.match(r"(participant|actor)\s+([^\s]+)", s)
        if m:
            nodes.add(m.group(2))
            continue
        m = re.match(r"([^\s:+-][^:]*?)\s*(?:-{1,2}>{1,2}|-{1,2}x|-{1,2}\)|<<-{1,2}>>)\s*[+-]?([^:]+?)\s*:", s)
        if m:
            nodes.update({m.group(1).strip(), m.group(2).strip()})
    return nodes


def state_nodes(src: str) -> set[str]:
    nodes = set()
    for _, s in _body_lines(src):
        if s.startswith(("stateDiagram", "direction", "note", "classDef", "class ", "}", "--")):
            continue
        m = re.match(r"state\s+(?:\"[^\"]*\"\s+as\s+)?([\w-]+)", s)
        if m:
            nodes.add(m.group(1))
            continue
        left = s.split(":", 1)[0]
        for part in re.split(r"\s*-->\s*", left):
            part = part.strip()
            if part and part != "[*]" and re.fullmatch(r"[\w-]+", part):
                nodes.add(part)
    return nodes


def er_nodes(src: str) -> set[str]:
    nodes = set()
    for _, s in _body_lines(src):
        m = re.match(r'("[^"]+"|[\w-]+)\s+[|}o][|o]?(?:--|\.\.)[|o]?[|{o]\s+("[^"]+"|[\w-]+)', s)
        if m:
            nodes.update({m.group(1), m.group(2)})
            continue
        m = re.match(r'("[^"]+"|[\w-]+)\s*\{\s*$', s)
        if m:
            nodes.add(m.group(1))
    return nodes


def class_nodes(src: str) -> set[str]:
    nodes = set()
    for _, s in _body_lines(src):
        m = re.match(r"class\s+([\w-]+)", s)
        if m:
            nodes.add(m.group(1))
            continue
        m = re.match(r'([\w-]+)\s*(?:"[^"]*"\s*)?(?:<\|--|--\|>|\*--|--\*|o--|--o|-->|<--|--|\.\.>|<\.\.|\.\.\|>|<\|\.\.|\.\.)\s*(?:"[^"]*"\s*)?([\w-]+)', s)
        if m:
            nodes.update({m.group(1), m.group(2)})
    return nodes


def gantt_nodes(src: str) -> set[str]:
    nodes = set()
    for _, s in _body_lines(src):
        if re.match(r"(gantt|title|dateFormat|axisFormat|excludes|section|todayMarker|tickInterval|weekday)\b", s):
            continue
        if ":" in s:
            nodes.add(s.split(":", 1)[0].strip())
    return nodes


def c4_nodes(src: str) -> set[str]:
    return {m.group(1) for _, s in _body_lines(src)
            for m in [re.match(r"(?:Person|System|Container|Component|SystemDb|ContainerDb|SystemQueue|ContainerQueue)(?:_Ext)?\(\s*([\w-]+)", s)] if m}


NODE_FUNCS = {
    "sequence": sequence_nodes, "state": state_nodes, "er": er_nodes,
    "class": class_nodes, "gantt": gantt_nodes, "c4": c4_nodes,
}


def nodes_of(src: str) -> set[str]:
    head = header(src)
    if head in ("flowchart", "graph"):
        return flow_nodes(src)[0]
    kind = "state" if head == "stateDiagram" else PROFILE_TYPES.get(head, "")
    fn = NODE_FUNCS.get(kind)
    return fn(src) if fn else set()


def level_of(src: str, default: str) -> str:
    m = re.search(r"^\s*%%\s*level:\s*(beginner|intermediate|advanced)\s*$", src, re.M)
    return m.group(1) if m else default


# ---------------------------------------------------------------- rules

def lint(d: Diagram, default_level: str = DEFAULT_LEVEL) -> list[Finding]:
    f: list[Finding] = []
    add = lambda rule, sev, msg: f.append(Finding(d.where, rule, sev, msg))  # noqa: E731
    head = header(d.src)
    level = level_of(d.src, default_level)

    # Profile
    if head in OFF_PROFILE:
        add("profile-type", "error", f"`{head}`: {OFF_PROFILE[head]}")
    elif head not in PROFILE_TYPES:
        add("profile-type", "error", f"`{head}` is outside the profile (flowchart, sequenceDiagram, stateDiagram-v2, erDiagram, classDiagram, gantt, C4Context)")
    if "@{" in d.src:
        add("profile-shape", "error", "`@{ shape: }` needs Mermaid 11.3+ and breaks terminal renderers; use a bracket shape")

    # Accessibility
    if not re.search(r"^\s*accTitle\s*:\s*\S", d.src, re.M):
        add("a11y-title", "error", "missing `accTitle:` (the short text alternative)")
    if not re.search(r"^\s*accDescr\s*(:\s*\S|\{)", d.src, re.M):
        add("a11y-descr", "error", "missing `accDescr` (what the diagram shows, in one or two sentences)")

    # Flowchart syntax traps
    if head in ("flowchart", "graph"):
        for i, s in _body_lines(d.src):
            if re.match(r"(subgraph|classDef|class|style|linkStyle|click)\b", s):
                continue
            unq = re.sub(r'"[^"]*"', '""', s)
            for m in re.finditer(r"[\w-](\(\(\(|\(\(|\(\[|\[\[|\[\(|\{\{|\[|\(|\{)\s*([^\s\"])", unq):
                add("quote-label", "error", f"line {i}: node label not quoted (`{m.group(0)}...`); write `id[\"label\"]`")
                break
            if re.search(r"\|\s*[^\"|\s][^|]*\|", unq):
                add("quote-label", "error", f"line {i}: edge label not quoted; write `-- \"label\" -->`")
            if re.search(r"(?:-{2,}|={2,}|-\.+-?)>?[ox][\w]", unq):
                add("banned-id", "error", f"line {i}: an id starting with `o` or `x` right after an arrow becomes a circle or cross edge; add a space or rename")
        if "end" in flow_nodes(d.src)[0]:
            add("banned-id", "error", "lowercase `end` as a node id breaks the flowchart; rename it (e.g. `done`)")

    # Size
    nodes = nodes_of(d.src)
    cap = NODE_CAPS[level]
    if len(nodes) > cap:
        add("node-cap", "error", f"{len(nodes)} nodes exceed the {level} cap of {cap}; split the diagram so each answers one question")

    # Legend: colour or style must be explained, never the only signal
    if re.search(r"^\s*classDef\s", d.src, re.M) and d.in_markdown:
        if not re.search(r"\b(legend|key)\b", d.before + "\n" + d.after + "\n" + d.src, re.I):
            add("legend", "error", "`classDef` styling is used but no legend or key explains it")

    # Explanation next to the diagram (Markdown only)
    if d.in_markdown:
        words = len(re.findall(r"[A-Za-z0-9']+", d.after))
        if words < MIN_EXPLANATION_WORDS:
            add("explanation", "error", f"only {words} words of explanation after the diagram; explain it in plain English ({MIN_EXPLANATION_WORDS}+ words)")
        if not d.before.strip():
            add("lead-sentence", "warning", "no sentence before the diagram stating the question it answers")
    return f


# ---------------------------------------------------------------- CLI

EXT = {".md", ".markdown", ".mmd", ".mermaid"}


def walk(p: Path) -> list[Path]:
    if p.is_dir():
        return sorted(q for q in p.rglob("*") if q.suffix in EXT and "node_modules" not in q.parts)
    return [p] if p.suffix in EXT else []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--level", choices=sorted(NODE_CAPS), default=DEFAULT_LEVEL)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    findings: list[Finding] = []
    count = 0
    for target in a.paths:
        p = Path(target)
        if not p.exists():
            print(f"no such path: {p}", file=sys.stderr)
            return 2
        for file in walk(p):
            for d in diagrams_in(file):
                count += 1
                findings.extend(lint(d, a.level))
    errors = sum(1 for x in findings if x.severity == "error")
    if a.json:
        print(json.dumps({"diagrams": count, "errors": errors, "findings": [asdict(x) for x in findings]}, indent=2))
    else:
        for x in findings:
            print(f"{x.severity.upper():7} {x.where} [{x.rule}] {x.message}")
        print(f"\n{count} diagrams, {errors} errors, {len(findings) - errors} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
