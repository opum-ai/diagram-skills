#!/usr/bin/env python3
"""Export Mermaid diagrams to SVG or PNG files, locally, on request only.

Diagrams normally stay as Mermaid source in Markdown, where GitHub and the
IDEs render them. Export is for places that need a picture file: slides,
email, Confluence. It uses @mermaid-js/mermaid-cli (mmdc), which needs a
headless Chromium, about 650 MB on disk, so nothing is installed until the
user asks.

Two rules make the export trustworthy:
  1. Every diagram is parse-checked first (mermaid-check.mjs). A diagram that
     fails is refused and nothing is rendered for it.
  2. mmdc can exit 0 while writing an SVG that only says "Syntax error"
     (seen in testing on a broken architecture-beta edge), so every SVG is
     inspected, and an error render counts as a failure.

Usage:
    diagram_export.py install [--yes]     show the cost; install only with --yes
    diagram_export.py status
    diagram_export.py uninstall           remove the cache directory, nothing else
    diagram_export.py export [--format svg|png|both] [--out DIR] <file.md|.mmd>...

The cache lives in $DIAGRAM_SKILLS_CACHE, else $XDG_CACHE_HOME/diagram-skills,
else ~/.cache/diagram-skills, under mmdc/.
Exit codes: 0 ok; 1 a diagram was refused or failed to render; 2 not installed
or environment error; 3 install needs --yes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diagram_lint as dl  # noqa: E402

MMDC_VERSION = "11.17.0"
PUPPETEER_VERSION = "24.43.1"
APPROX_MB = 650
MARKER = ".diagram-skills-export"
ERROR_RENDER = re.compile(r"Syntax error in text|aria-roledescription=\"error\"|class=\"error-icon\"", re.I)


def parse_pin() -> str:
    """The Mermaid version the parse check uses; the renderer is pinned to match."""
    return json.loads((HERE / "package.json").read_text())["dependencies"]["mermaid"]


def cache_dir() -> Path:
    base = os.environ.get("DIAGRAM_SKILLS_CACHE") or os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(Path.home(), ".cache"), "diagram-skills")
    return Path(base) / "mmdc"


def env_for(cache: Path) -> dict:
    return {**os.environ, "PUPPETEER_CACHE_DIR": str(cache / "browsers")}


def installed(cache: Path) -> bool:
    return (cache / MARKER).exists() and (cache / "node_modules" / ".bin" / "mmdc").exists()


def du_mb(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file() and not f.is_symlink()) // (1024 * 1024)


# ---------------------------------------------------------------- install / uninstall

def cmd_install(yes: bool) -> int:
    cache = cache_dir()
    pin = parse_pin()
    print(f"Image export installs @mermaid-js/mermaid-cli {MMDC_VERSION} (Mermaid pinned to {pin}, the parse-check "
          f"version) and a headless Chromium into:\n  {cache}\nThis takes about {APPROX_MB} MB of disk. "
          f"`diagram_export.py uninstall` removes it again.")
    if installed(cache):
        print("Already installed.")
        return 0
    if not yes:
        print("Nothing installed. Re-run with --yes to install.")
        return 3
    if not shutil.which("npm"):
        print("npm is not available; cannot install.", file=sys.stderr)
        return 2
    cache.mkdir(parents=True, exist_ok=True)
    (cache / MARKER).write_text("Created by diagram-skills diagram_export.py; safe to delete.\n")
    (cache / "package.json").write_text(json.dumps({
        "name": "diagram-skills-export", "private": True,
        "dependencies": {"@mermaid-js/mermaid-cli": MMDC_VERSION, "puppeteer": PUPPETEER_VERSION},
        "overrides": {"mermaid": pin},
    }, indent=2) + "\n")
    steps = [
        ["npm", "install", "--no-audit", "--no-fund", "--ignore-scripts"],
        ["npx", "--no-install", "puppeteer", "browsers", "install", "chrome-headless-shell"],
    ]
    for step in steps:
        r = subprocess.run(step, cwd=cache, env=env_for(cache))
        if r.returncode != 0:
            print(f"install step failed: {' '.join(step)}", file=sys.stderr)
            return 2
    got = json.loads((cache / "node_modules" / "mermaid" / "package.json").read_text())["version"]
    if got != pin:
        print(f"renderer resolved Mermaid {got}, not the parse pin {pin}; refusing to use it", file=sys.stderr)
        return 2
    print(f"Installed ({du_mb(cache)} MB). Renderer Mermaid {got} matches the parse check.")
    return 0


def cmd_uninstall() -> int:
    cache = cache_dir()
    if not cache.exists():
        print(f"Nothing to remove at {cache}.")
        return 0
    if not (cache / MARKER).exists():
        print(f"{cache} was not created by this tool (no {MARKER} marker); leaving it alone.", file=sys.stderr)
        return 2
    size = du_mb(cache)
    shutil.rmtree(cache)
    print(f"Removed {cache} ({size} MB).")
    return 0


def cmd_status() -> int:
    cache = cache_dir()
    if installed(cache):
        print(f"installed at {cache} ({du_mb(cache)} MB); mmdc {MMDC_VERSION}, Mermaid {parse_pin()}")
        return 0
    print(f"not installed (would use {cache}, about {APPROX_MB} MB)")
    return 2


# ---------------------------------------------------------------- export

def is_error_render(svg_text: str) -> bool:
    return bool(ERROR_RENDER.search(svg_text))


def render(cache: Path, src: Path, out: Path) -> tuple[bool, str]:
    mmdc = cache / "node_modules" / ".bin" / "mmdc"
    r = subprocess.run([str(mmdc), "-q", "-i", str(src), "-o", str(out), "-b", "white"],
                       capture_output=True, text=True, env=env_for(cache))
    if r.returncode != 0 or not out.exists():
        lines = (r.stderr or r.stdout).strip().splitlines()
        return False, lines[-1] if lines else "mmdc failed"
    return True, ""


def cmd_export(paths: list[str], fmt: str, out_dir: str) -> int:
    cache = cache_dir()
    if not installed(cache):
        print("Image export is not installed. Run `diagram_export.py install` to see the cost, "
              "then `install --yes` if the user wants it.", file=sys.stderr)
        return 2
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    checker = HERE / "mermaid-check.mjs"
    bad = 0
    for target in paths:
        p = Path(target)
        if not p.exists():
            print(f"no such path: {p}", file=sys.stderr)
            return 2
        for file in dl.walk(p):
            for d in dl.diagrams_in(file):
                line = d.where.rsplit(":", 1)[1] if ":" in d.where and file.suffix in (".md", ".markdown") else "1"
                stem = f"{file.stem}-{line}"
                with tempfile.TemporaryDirectory() as tmp:
                    mmd = Path(tmp) / f"{stem}.mmd"
                    mmd.write_text(d.src)
                    r = subprocess.run(["node", str(checker), str(mmd)], capture_output=True, text=True)
                    if r.returncode == 2:
                        print(f"ENV     {d.where}: parse check could not run ({r.stdout.strip().splitlines()[-1:]})")
                        return 2
                    if r.returncode != 0:
                        print(f"REFUSED {d.where}: does not parse; nothing rendered")
                        bad += 1
                        continue
                    svg = out / f"{stem}.svg"
                    ok, why = render(cache, mmd, svg)
                    if ok and is_error_render(svg.read_text(errors="replace")):
                        ok, why = False, "mmdc wrote an error render"
                    if not ok:
                        svg.unlink(missing_ok=True)
                        print(f"FAILED  {d.where}: {why}")
                        bad += 1
                        continue
                    made = [svg]
                    if fmt in ("png", "both"):
                        png = out / f"{stem}.png"
                        ok, why = render(cache, mmd, png)
                        if not ok:
                            print(f"FAILED  {d.where}: PNG: {why}")
                            bad += 1
                            continue
                        made.append(png)
                    if fmt == "png":
                        svg.unlink()
                        made = made[1:]
                    print(f"OK      {d.where} -> {', '.join(str(m) for m in made)}")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("install")
    i.add_argument("--yes", action="store_true")
    sub.add_parser("status")
    sub.add_parser("uninstall")
    e = sub.add_parser("export")
    e.add_argument("paths", nargs="+")
    e.add_argument("--format", choices=["svg", "png", "both"], default="svg")
    e.add_argument("--out", default="diagram-exports")
    a = ap.parse_args(argv)
    if a.cmd == "install":
        return cmd_install(a.yes)
    if a.cmd == "uninstall":
        return cmd_uninstall()
    if a.cmd == "status":
        return cmd_status()
    return cmd_export(a.paths, a.format, a.out)


if __name__ == "__main__":
    sys.exit(main())
