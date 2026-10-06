#!/usr/bin/env python3
"""List what a repository actually contains, as candidate nodes for a C4 diagram.

Architecture diagrams fail when the model draws the system it expects instead
of the one in front of it (template components). This walks the tree and
reports only what has evidence: deployable units (a manifest or Dockerfile),
datastores and external services (named in compose files or dependencies), and
the docs bundle. Every item carries the path to cite in a `%% ref` line.

It proposes; it does not decide. Grouping units into containers, naming them
for the reader, and choosing what to leave out stay with the skill.

Usage: repo_inventory.py [--root DIR] [--max-depth N]
Prints JSON: {root, units[], datastores[], externals[], docs[]}.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "target",
             ".next", ".turbo", "vendor", ".tox", ".mypy_cache", ".pytest_cache", "coverage"}
MANIFESTS = {
    "package.json": "node", "pyproject.toml": "python", "setup.py": "python", "requirements.txt": "python",
    "go.mod": "go", "Cargo.toml": "rust", "pom.xml": "java", "build.gradle": "java", "build.gradle.kts": "kotlin",
    "Gemfile": "ruby", "composer.json": "php", "mix.exs": "elixir", "Dockerfile": "container",
    ".claude-plugin/plugin.json": "claude-plugin", "SKILL.md": "claude-skill",
}
DATASTORES = {
    "postgres": r"\b(postgres(ql)?|psycopg2?|asyncpg|pg)\b", "mysql": r"\b(mysql|mariadb|pymysql)\b",
    "redis": r"\b(redis|ioredis)\b", "mongodb": r"\b(mongo(db)?|mongoose|pymongo)\b",
    "sqlite": r"\bsqlite3?\b", "kafka": r"\b(kafka|kafkajs|confluent-kafka)\b",
    "rabbitmq": r"\b(rabbitmq|amqplib|pika)\b", "elasticsearch": r"\b(elasticsearch|opensearch)\b",
    "s3": r"\b(@aws-sdk/client-s3|boto3|s3)\b",
}
EXTERNALS = {
    "Stripe": r"\bstripe\b", "Twilio": r"\btwilio\b", "SendGrid": r"\b(sendgrid|@sendgrid/mail)\b",
    "Anthropic API": r"\b(anthropic|@anthropic-ai/sdk)\b", "OpenAI API": r"\bopenai\b",
    "GitHub": r"\b(octokit|@octokit/\w+|PyGithub)\b", "Slack": r"\b(@slack/\w+|slack[-_]sdk|slack_bolt)\b",
    "Auth0": r"\bauth0\b", "Sentry": r"\b(@sentry/\w+|sentry[-_]sdk)\b",
}
DEP_FILES = ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml", "Gemfile", "composer.json", "pom.xml")


def walk(root: Path, max_depth: int):
    stack = [(root, 0)]
    while stack:
        d, depth = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.is_dir():
                if e.name not in SKIP_DIRS and not e.name.startswith(".") or e.name in (".claude-plugin", ".github"):
                    if depth < max_depth:
                        stack.append((e, depth + 1))
            else:
                yield e


def unit_name(manifest: Path) -> str | None:
    text = manifest.read_text(encoding="utf-8", errors="replace")
    if manifest.name.endswith(".json"):
        try:
            return json.loads(text).get("name")
        except (json.JSONDecodeError, AttributeError):
            return None
    for pat in (r'^\s*name\s*=\s*"([^"]+)"', r"^module\s+(\S+)", r"^name:\s*(\S+)", r"<artifactId>([^<]+)</artifactId>"):
        m = re.search(pat, text, re.M)
        if m:
            return m.group(1)
    return None


def compose_services(f: Path) -> list[dict]:
    out, cur, in_services = [], None, False
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^services:\s*$", line):
            in_services = True
            continue
        if in_services and re.match(r"^\S", line):
            in_services = False
        m = re.match(r"^  ([\w.-]+):\s*$", line) if in_services else None
        if m:
            cur = {"service": m.group(1), "image": None, "build": False}
            out.append(cur)
        elif cur and (mi := re.match(r"^\s+image:\s*['\"]?([^'\"\s]+)", line)):
            cur["image"] = mi.group(1)
        elif cur and re.match(r"^\s+build:", line):
            cur["build"] = True
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--max-depth", type=int, default=4)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    rel = lambda p: str(p.relative_to(root))  # noqa: E731
    units: dict[str, dict] = {}
    datastores: dict[str, set] = {}
    externals: dict[str, set] = {}
    docs: list[str] = []
    for f in walk(root, a.max_depth):
        r = rel(f)
        kind = MANIFESTS.get(f.name) or MANIFESTS.get(r if r.startswith(".claude-plugin/") else "")
        if kind:
            d = rel(f.parent) if f.parent != root else "."
            if kind == "claude-plugin":
                d = "."
            u = units.setdefault(d, {"path": d, "kinds": [], "manifests": [], "name": None})
            if kind not in u["kinds"]:
                u["kinds"].append(kind)
            u["manifests"].append(r)
            if not u["name"] and kind not in ("container", "claude-skill"):
                u["name"] = unit_name(f)
        if re.match(r"(docker-)?compose(\.[\w-]+)?\.ya?ml$", f.name):
            for s in compose_services(f):
                img = (s["image"] or "").lower()
                hit = next((n for n, pat in DATASTORES.items() if re.search(pat, img)), None)
                if hit:
                    datastores.setdefault(hit, set()).add(f"{r}#{s['service']}")
                elif s["build"] or s["image"]:
                    units.setdefault(f"compose:{s['service']}", {"path": r, "kinds": ["compose-service"],
                                     "manifests": [r], "name": s["service"]})
        if f.name in DEP_FILES:
            text = f.read_text(encoding="utf-8", errors="replace")
            for n, pat in DATASTORES.items():
                if re.search(pat, text, re.I):
                    datastores.setdefault(n, set()).add(r)
            for n, pat in EXTERNALS.items():
                if re.search(pat, text, re.I):
                    externals.setdefault(n, set()).add(r)
        if f.suffix == ".md" and r.startswith("docs/") and f.name != "index.md":
            docs.append(r[len("docs/"):-3])
    print(json.dumps({
        "root": str(root),
        "units": sorted(units.values(), key=lambda u: u["path"]),
        "datastores": [{"name": n, "evidence": sorted(e)} for n, e in sorted(datastores.items())],
        "externals": [{"name": n, "evidence": sorted(e)} for n, e in sorted(externals.items())],
        "docs": sorted(docs),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
