#!/usr/bin/env python3
"""Grade one eval run objectively, without trusting the agent's own claims.

A run directory holds `outputs/answer.md` (the agent's final reply) and
`repo/` (the workspace after the run). This re-runs the parse check and reads
the diagrams itself, then compares them with the truth recorded for the case
in evals/evals.json. For plan cases that truth is Quest's live records in the
run's own workspace.

Graders are convention-neutral: they do not require the suite's `%% ref` or
`%% level` lines, so the baseline arm is judged on the same terms as the
with-skill arm. Nodes are matched to real components by their ids and labels.

Usage: grade.py <run-dir> --eval <id|name> [--evals evals/evals.json]
Writes <run-dir>/grading.json as {expectations: [{text, passed, evidence}], summary}.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "skills" / "diagram-review" / "scripts"
sys.path.insert(0, str(ENGINE))
import diagram_lint as dl  # noqa: E402
from diagram_lint import flow_edges  # noqa: E402

CAPS = dl.NODE_CAPS
MIN_WORDS = 30
CHOSEN = re.compile(r"(?<!not )(?<!not\s)\b(chosen|selected|picked|winner|we chose|decision|accepted|✅|✔)", re.I)
NEGATED = re.compile(r"\b(not chosen|not picked|not selected|rejected|ruled out|declined|dropped)\b", re.I)
STATUS_WORD = re.compile(r"\b(done|complete[d]?|in progress|in-progress|to ?do|not started|open|blocked|ready|finished|✅)\b", re.I)


# ---------------------------------------------------------------- reading diagrams

def fences(path: Path) -> list[dl.Diagram]:
    return dl.diagrams_in(path) if path.exists() else []


def labels(src: str) -> dict[str, str]:
    """Node id -> label text, for every diagram type the suite uses."""
    out: dict[str, str] = {}
    opener = r'\b([A-Za-z_][\w-]*)\s*(\(\[|\[\(|\[\[|\(\(|\{\{|\[|\(|\{|>)\s*'
    quoted = re.compile(opener + r'"([^"]*)"')  # a quoted label runs to its closing quote, ")" included
    bare = re.compile(opener + r'([^"\])}]*)(\]\)|\)\]|\]\]|\)\)|\}\}|\]|\)|\})')
    for _, s in dl._body_lines(src):
        for m in quoted.finditer(s):
            out.setdefault(m.group(1), m.group(3))
        for m in bare.finditer(s):
            out.setdefault(m.group(1), m.group(3))
        m = re.match(r'(?:participant|actor)\s+(\S+)\s+as\s+(.+)$', s)
        if m:
            out[m.group(1)] = m.group(2)
        m = re.match(r'state\s+"([^"]+)"\s+as\s+(\S+)', s)
        if m:
            out[m.group(2)] = m.group(1)
        m = re.match(r'([\w-]+)\s*:\s*(.+)$', s)
        if m and "-->" not in s and not s.startswith(("accTitle", "accDescr", "title")):
            out.setdefault(m.group(1), m.group(2))
    return out


def edge_labels(src: str) -> dict[str, str]:
    """Target node id -> concatenated labels of edges pointing at it."""
    out: dict[str, str] = {}
    for _, s in dl._body_lines(src):
        s = re.sub(r'[\[({]+"[^"]*"[\])}]+|[\[({]+[^"\[\](){}]*[\])}]+', "", s)  # drop node shapes, keep edge labels
        for m in re.finditer(r'(\w+)\s*(?:--|==|-\.)\s*"([^"]*)"\s*(?:-->|==>|\.->)\s*(\w+)', s):
            out[m.group(3)] = out.get(m.group(3), "") + " " + m.group(2)
        for m in re.finditer(r'(\w+)\s*(?:-->|==>|-\.->)\s*\|"?([^|"]*)"?\|\s*(\w+)', s):
            out[m.group(3)] = out.get(m.group(3), "") + " " + m.group(2)
    return out


def node_texts(d: dl.Diagram) -> dict[str, str]:
    lab = labels(d.src)
    return {n: f"{n.replace('_', ' ')} {lab.get(n, '')}".lower() for n in dl.nodes_of(d.src)}


def classify(node: str, text: str, groups: dict[str, list[str]]) -> str | None:
    """Which real thing a node is: judged on its id first, then the first line of its
    label, then the whole label. A label's later lines are descriptions ("charges the
    customer's card") whose nouns would otherwise outvote the name on the first line."""
    label = text.split(" ", 1)[1] if " " in text else ""
    first = re.split(r"<br\s*/?>|\n", label)[0]
    for candidate in (node.replace("_", " ").lower(), first, label):
        k = best_match(candidate, groups)
        if k:
            return k
    return None


def best_match(text: str, groups: dict[str, list[str]]) -> str | None:
    best, best_len = None, 0
    for key, aliases in groups.items():
        for a in aliases:
            if re.search(rf"(?<![\w]){re.escape(a.lower())}(?![\w])", text) and len(a) > best_len:
                best, best_len = key, len(a)
    return best


def any_word(text: str, words: list[str]) -> str | None:
    for w in words:
        if re.search(rf"(?<![\w]){re.escape(w.lower())}", text):
            return w
    return None


def state_edges(src: str) -> set[tuple[str, str]]:
    if dl.header(src).startswith("stateDiagram"):
        out = set()
        for _, s in dl._body_lines(src):
            m = re.match(r"([\w\[\]*-]+)\s*-->\s*([\w\[\]*-]+)", s)
            if m and "[*]" not in (m.group(1), m.group(2)):
                out.add((m.group(1), m.group(2)))
        return out
    return flow_edges(src)


def er_pairs(src: str) -> list[tuple[str, str, str]]:
    out = []
    for _, s in dl._body_lines(src):
        m = re.match(r'("?[\w-]+"?)\s+([|}o][|o]?(?:--|\.\.)[|o]?[|{o])\s+("?[\w-]+"?)', s)
        if m:
            out.append((m.group(1).strip('"'), m.group(3).strip('"'), m.group(2)))
    return out


def parse_ok(path: Path) -> tuple[bool, str]:
    r = subprocess.run(["node", str(ENGINE / "mermaid-check.mjs"), str(path)], capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    if r.returncode == 2:
        return False, f"environment error, not a verdict: {tail}"
    fails = [ln[:160] for ln in r.stdout.splitlines() if ln.startswith("FAIL")]
    return r.returncode == 0, "; ".join(fails) or tail


# ---------------------------------------------------------------- common expectations

def common(ds: list[dl.Diagram], src_file: Path, level: str, exp: list) -> None:
    if not ds:
        exp.append(("Every diagram parses under mermaid 11.17.2", False, "no ```mermaid fence found"))
        exp.append(("Every diagram has accTitle and accDescr", False, "no diagram"))
        exp.append((f"Every diagram stays within the {level} node cap ({CAPS[level]})", False, "no diagram"))
        exp.append((f"A plain-English explanation of at least {MIN_WORDS} words accompanies the diagram", False, "no diagram"))
        return
    ok, ev = parse_ok(src_file)
    exp.append(("Every diagram parses under mermaid 11.17.2", ok, ev))
    missing = [d.where for d in ds if not (re.search(r"^\s*accTitle\s*:\s*\S", d.src, re.M) and re.search(r"^\s*accDescr\s*(:\s*\S|\{)", d.src, re.M))]
    exp.append(("Every diagram has accTitle and accDescr", not missing, f"missing in {missing}" if missing else f"{len(ds)} diagram(s) carry both"))
    sizes = [len(dl.nodes_of(d.src)) for d in ds]
    exp.append((f"Every diagram stays within the {level} node cap ({CAPS[level]})", max(sizes) <= CAPS[level], f"node counts {sizes}"))
    words = [len(re.findall(r"[A-Za-z0-9']+", d.before + " " + d.after)) for d in ds]
    exp.append((f"A plain-English explanation of at least {MIN_WORDS} words accompanies the diagram", min(words) >= MIN_WORDS, f"prose words around each diagram: {words}"))


# ---------------------------------------------------------------- per-kind truth

def g_components(ds, truth, cfg, exp):
    groups = {k: v["aliases"] for k, v in cfg["components"][truth["set"]].items()}
    invented = cfg["components"]["invented"]
    found, unknown, inv = set(), [], []
    for d in ds:
        if dl.header(d.src) not in ("flowchart", "graph", "C4Context", "C4Container"):
            continue
        for n, text in node_texts(d).items():
            w = any_word(text, invented)
            if w:
                inv.append(f"{n} ({w})")
                continue
            k = classify(n, text, groups)
            (found.add(k) if k else unknown.append(n))
    exp.append(("Every node is a component that exists in the repository", not unknown and not inv, f"unmatched: {unknown}; invented: {inv}" if unknown or inv else f"matched: {sorted(found)}"))
    if truth.get("require_all"):
        req = [k for k, v in cfg["components"][truth["set"]].items() if v["required"]]
        miss = [k for k in req if k not in found]
        exp.append(("All six real components are drawn (web, orders API, worker, Postgres, Stripe, ShipEngine)", not miss, f"missing: {miss}" if miss else "all present"))
    if truth.get("require"):
        miss = [k for k in truth["require"] if k not in found]
        exp.append(("Stripe and ShipEngine are both drawn", not miss, f"missing: {miss}" if miss else "both present"))
    exp.append(("No invented components (cache, queue, gateway, ...)", not inv, f"invented: {inv}" if inv else "none"))


def g_states(ds, truth, exp, label_prefix=""):
    states = truth["states"]
    seen, invented, edges = set(), [], set()
    for d in ds:
        texts = node_texts(d)
        idmap = {}
        for n, t in texts.items():
            w = any_word(t, truth.get("invented", []))
            if w:
                invented.append(n)
            k = classify(n, t, states)
            if k:
                seen.add(k)
                idmap[n] = k
        for a, b in state_edges(d.src):
            if a in idmap and b in idmap:
                edges.add((idmap[a], idmap[b]))
    miss_states = [s for s in states if s not in seen]
    if "invented" in truth:
        exp.append(("All five real statuses are drawn and no invented status is", not miss_states and not invented, f"missing {miss_states}; invented {invented}"))
    else:
        exp.append((f"{label_prefix}keeps every real status", not miss_states, f"missing {miss_states}" if miss_states else "all five present"))
    req = [tuple(e) for e in truth["required_edges"]]
    miss = [e for e in req if e not in edges]
    text = "Every transition allowed in states.py is drawn" if not label_prefix else f"{label_prefix}keeps every real transition"
    exp.append((text, not miss, f"missing {miss}" if miss else f"drawn {sorted(edges)}"))
    if "forbidden_edges" in truth:
        bad = [tuple(e) for e in truth["forbidden_edges"] if tuple(e) in edges]
        exp.append(("No transition the code forbids is drawn", not bad, f"forbidden drawn: {bad}" if bad else "none"))


def g_sequence(ds, truth, exp):
    parts = truth["participants"]
    seen, inv = set(), []
    alltext = ""
    for d in ds:
        alltext += d.src.lower()
        if dl.header(d.src) != "sequenceDiagram":
            continue
        for n, t in node_texts(d).items():
            w = any_word(t, truth["invented"])
            if w:
                inv.append(f"{n} ({w})")
            k = classify(n, t, parts)
            if k:
                seen.add(k)
    miss = [p for p in parts if p not in seen]
    exp.append(("Storefront, orders API, Stripe and Postgres are all participants", not miss, f"missing {miss}" if miss else "all present"))
    err = re.search(r"^\s*(alt|opt|break)\b", alltext, re.M) and any_word(alltext, truth["error_path"])
    exp.append(("The declined-payment path is drawn (alt/else with 402 or payment_failed)", bool(err), "alt/opt/break block with a decline marker" if err else "no alt/opt/break block naming the decline"))
    exp.append(("No invented participants (inventory, cache, queue, worker, ...)", not inv, f"invented: {inv}" if inv else "none"))


def g_decision(ds, truth, exp):
    opts = truth["options"]
    seen, chosen_marked, inv, jargon = set(), set(), [], []
    for d in ds:
        texts, elab = node_texts(d), edge_labels(d.src)
        for n, t in texts.items():
            w = any_word(t, truth.get("invented", []))
            if w:
                inv.append(n)
            k = classify(n, t, opts)
            if not k:
                continue
            seen.add(k)
            full = t + " " + elab.get(n, "").lower()
            if CHOSEN.search(full) and not NEGATED.search(full):
                chosen_marked.add(k)
            if truth.get("jargon"):
                j = any_word(labels(d.src).get(n, "").lower(), truth["jargon"])
                if j:
                    jargon.append(f"{n} ({j})")
    miss = [o for o in opts if o not in seen]
    exp.append(("All three options from the ADR are drawn and no invented option is", not miss and not inv, f"missing {miss}; invented {inv}"))
    exp.append(("The chosen option is " + ("Debezium CDC" if not truth.get("jargon") else "the live/CDC one") + ", marked in text",
                truth["chosen"] in chosen_marked, f"options marked chosen in text: {sorted(chosen_marked)}"))
    if truth.get("jargon"):
        exp.append(("Diagram labels avoid jargon (Debezium, CDC, WAL, Postgres, ETL)", not jargon, f"jargon: {jargon}" if jargon else "none"))
    else:
        wrong = sorted(chosen_marked - {truth["chosen"]})
        exp.append(("No rejected option is marked as chosen", not wrong, f"wrongly marked: {wrong}" if wrong else "none"))


def quest_tasks(repo: Path) -> dict[str, dict]:
    r = subprocess.run(["quest", "task", "list", "--json"], cwd=repo, capture_output=True, text=True)
    return {t["id"]: t for t in json.loads(r.stdout)["data"]} if r.returncode == 0 else {}


def task_of(node: str, text: str, tasks: dict[str, dict]) -> str | None:
    m = re.search(r"\bshop[\s_-]?(\d+)\b", f"{node} {text}", re.I)
    if m:
        return f"SHOP-{m.group(1)}"
    words = set(re.findall(r"[a-z]+", text))
    for tid, t in tasks.items():
        tw = set(re.findall(r"[a-z]+", t["title"].lower())) - {"the", "a", "an", "when", "is", "and", "from"}
        if tw and len(tw & words) / len(tw) >= 0.7:
            return tid
    return None


def g_plan(ds, truth, repo, exp):
    tasks = quest_tasks(repo)
    if not tasks:
        exp.append(("Quest records are readable in the run workspace", False, "quest task list failed"))
        return
    drawn, edges, nostatus = set(), set(), []
    for d in ds:
        texts = node_texts(d)
        idmap = {n: task_of(n, t, tasks) for n, t in texts.items()}
        for n, tid in idmap.items():
            if tid:
                drawn.add(tid)
                if truth.get("status_in_text") and not STATUS_WORD.search(labels(d.src).get(n, "")):
                    nostatus.append(tid)
        for a, b in flow_edges(d.src):
            if idmap.get(a) and idmap.get(b):
                edges.add(frozenset((idmap[a], idmap[b])))
    exp_set = set(truth["expected_tasks"])
    miss = sorted(exp_set - drawn)
    extra = sorted(drawn - exp_set - set(truth.get("optional_tasks", [])))
    if "SHOP-2" in truth["excluded_tasks"]:
        exp.append(("Every open launch task is drawn", not miss, f"missing {miss}" if miss else "all drawn"))
        done = sorted(drawn & set(truth["excluded_tasks"]))
        exp.append(("No completed task is drawn", not done, f"done tasks drawn: {done}" if done else "none"))
    else:
        exp.append(("Every Payments subtask is drawn and no task outside the epic is", not miss and not extra, f"missing {miss}; extra {extra}"))
    expected = {frozenset((dep, t)) for t in drawn for dep in tasks.get(t, {}).get("dependencies", []) if dep in drawn}
    parent = {frozenset((t, tasks[t].get("parentId"))) for t in drawn if tasks.get(t, {}).get("parentId") in drawn}
    extra_e = sorted(tuple(sorted(e)) for e in edges - expected - parent)
    miss_e = sorted(tuple(sorted(e)) for e in expected - edges)
    exp.append(("Drawn edges equal the dependencies recorded in Quest", not extra_e and not miss_e, f"missing {miss_e}; not in Quest {extra_e}"))
    if truth.get("status_in_text"):
        exp.append(("Each task's status is written in its label", not nostatus, f"no status word: {sorted(set(nostatus))}" if nostatus else "every task label carries its status"))


def g_er(ds, truth, exp):
    ents = truth["entities"]
    seen, inv, pairs, optional_ok = set(), [], set(), {}
    for d in ds:
        texts = node_texts(d)
        idmap = {}
        for n, t in texts.items():
            w = any_word(n.lower(), truth["invented"]) or any_word(t, truth["invented"])
            if w:
                inv.append(n)
                continue
            k = classify(n, t, ents)
            if k:
                seen.add(k)
                idmap[n] = k
        for a, b, card in er_pairs(d.src):
            ka, kb = idmap.get(a) or best_match(a.lower(), ents), idmap.get(b) or best_match(b.lower(), ents)
            if ka and kb:
                key = frozenset((ka, kb))
                pairs.add(key)
                optional_ok[key] = optional_ok.get(key, False) or ("o|" in card or "|o" in card)
        if dl.header(d.src) != "erDiagram":
            for a, b in flow_edges(d.src):
                ka, kb = idmap.get(a), idmap.get(b)
                if ka and kb:
                    pairs.add(frozenset((ka, kb)))
    req = truth.get("require") or list(ents)
    miss = [e for e in req if e not in seen]
    if truth.get("require"):
        exp.append(("Customers and orders are drawn and no invented record type is", not miss and not inv, f"missing {miss}; invented {inv}"))
        return
    exp.append(("All five tables are drawn and no invented or dropped table is", not miss and not inv, f"missing {miss}; invented {inv}"))
    want = {frozenset(p) for p in truth["relationships"]}
    exp.append(("Exactly the four foreign-key relationships are drawn", pairs == want,
                f"missing {sorted(tuple(sorted(p)) for p in want - pairs)}; extra {sorted(tuple(sorted(p)) for p in pairs - want)}"))
    for a, b in truth.get("optional", []):
        k = frozenset((a, b))
        exp.append(("The orders-coupons relationship is drawn as optional", bool(optional_ok.get(k)), "zero-or-one marker present" if optional_ok.get(k) else "drawn as mandatory or not drawn"))


def g_review(ds, answer: Path, truth, exp):
    text = answer.read_text(encoding="utf-8").lower() if answer.exists() else ""
    flagged_cache = ("redis" in text or "cache" in text) and re.search(r"(not (in|present|part|used|exist)|doesn.t exist|does not exist|no (redis|cache)|invent|nothing in|isn.t (in|there|real|used)|no evidence|not backed|unsupported|no such)", text)
    exp.append(("The review flags the Redis cache as not in the repository", bool(flagged_cache), "flagged" if flagged_cache else "not flagged as absent"))
    cause = re.search(r"(quot|parenthes)", text)
    exp.append(("The review identifies the unquoted label with parentheses as why it does not render", bool(cause), "names quoting or parentheses" if cause else "cause not identified"))
    # The corrected diagram is the reply's last mermaid fence. Earlier fences may quote
    # the original, broken one, so only the last is parsed and judged.
    if not ds:
        for t in ("A corrected diagram is offered and it parses", "The corrected diagram drops the cache", "The corrected diagram has accTitle and accDescr"):
            exp.append((t, False, "no corrected diagram in the reply"))
        return
    last = ds[-1]
    tmp = answer.parent / ".corrected.mmd"
    tmp.write_text(last.src)
    ok, ev = parse_ok(tmp)
    tmp.unlink()
    exp.append(("A corrected diagram is offered and it parses", ok, ev))
    has_cache = any_word(last.src.lower(), truth["corrected_must_not_contain"])
    exp.append(("The corrected diagram drops the cache", not has_cache, "cache still drawn" if has_cache else "no cache"))
    acc = re.search(r"^\s*accTitle\s*:", last.src, re.M) and re.search(r"^\s*accDescr\s*(:|\{)", last.src, re.M)
    exp.append(("The corrected diagram has accTitle and accDescr", bool(acc), "present" if acc else "missing"))


# ---------------------------------------------------------------- main

def grade(run: Path, case: dict, cfg: dict) -> dict:
    answer = run / "outputs" / "answer.md"
    repo = run / "repo"
    truth, level = case["truth"], case["level"]
    exp: list = []
    kind = truth["kind"]
    if kind == "fix":
        f = repo / truth["file"]
        ds = fences(f)
        ok, ev = parse_ok(f) if ds else (False, "no mermaid fence left in the file")
        exp.append(("docs/order-flow.md now parses under mermaid 11.17.2", ok, ev))
        acc = ds and all(re.search(r"^\s*accTitle\s*:", d.src, re.M) and re.search(r"^\s*accDescr\s*(:|\{)", d.src, re.M) for d in ds)
        exp.append(("docs/order-flow.md diagrams have accTitle and accDescr", bool(acc), "present" if acc else "missing"))
        g_states(ds, truth, exp, label_prefix="The fixed diagram ")
    elif kind == "review":
        g_review(fences(answer), answer, truth, exp)
    else:
        ds = fences(answer)
        common(ds, answer, level, exp)
        if ds:
            {"components": lambda: g_components(ds, truth, cfg, exp),
             "states": lambda: g_states(ds, truth, exp),
             "sequence": lambda: g_sequence(ds, truth, exp),
             "decision": lambda: g_decision(ds, truth, exp),
             "plan": lambda: g_plan(ds, truth, repo, exp),
             "er": lambda: g_er(ds, truth, exp)}[kind]()
    expectations = [{"text": t, "passed": bool(p), "evidence": e} for t, p, e in exp]
    passed = sum(e["passed"] for e in expectations)
    return {"expectations": expectations,
            "summary": {"passed": passed, "failed": len(expectations) - passed, "total": len(expectations),
                        "pass_rate": round(passed / len(expectations), 4) if expectations else 0.0}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("run")
    ap.add_argument("--eval", required=True)
    ap.add_argument("--evals", default=str(ROOT / "evals" / "evals.json"))
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.evals).read_text())
    case = next((e for e in cfg["evals"] if str(e["id"]) == a.eval or e["name"] == a.eval), None)
    if not case:
        print(f"no eval {a.eval}", file=sys.stderr)
        return 2
    run = Path(a.run)
    result = grade(run, case, cfg)
    (run / "grading.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    s = result["summary"]
    print(f"{case['name']}: {s['passed']}/{s['total']}")
    for e in result["expectations"]:
        print(f"  {'PASS' if e['passed'] else 'FAIL'} {e['text']} - {e['evidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
