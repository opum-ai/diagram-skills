#!/usr/bin/env bash
# Prove the opt-in image export both ways. Needs the renderer installed
# (diagram_export.py install --yes, about 650 MB), so CI skips it; run it by
# hand after installing. Checks: a valid diagram exports to SVG and PNG; a
# broken one is refused; mmdc's own "success" on a broken architecture-beta
# edge (an SVG that only says "Syntax error") is caught as an error render.
set -u
cd "$(dirname "$0")/.."
X="python3 skills/diagram-review/scripts/diagram_export.py"
if ! $X status >/dev/null 2>&1; then echo "SKIP: image export not installed"; exit 0; fi
out="$(mktemp -d)"; rc=0
$X export --format both --out "$out" skills/diagram-decision/examples/notation-decision.md >/dev/null
[ -s "$out/notation-decision-13.svg" ] && [ -s "$out/notation-decision-13.png" ] && echo "ok   valid diagram exported to SVG and PNG" || { echo "FAIL valid diagram not exported"; rc=1; }
$X export --out "$out" tests/fixtures/mermaid/fail/flowchart-unquoted-parens.mmd | grep -q '^REFUSED' && [ ! -e "$out/flowchart-unquoted-parens-1.svg" ] \
  && echo "ok   broken diagram refused, nothing rendered" || { echo "FAIL broken diagram not refused"; rc=1; }
python3 - "$out" <<'PY' && echo "ok   mmdc false success caught as an error render" || rc=1
import sys; sys.path.insert(0, "skills/diagram-review/scripts")
from pathlib import Path
import diagram_export as de
svg = Path(sys.argv[1]) / "arch.svg"
ok, _ = de.render(de.cache_dir(), Path("tests/fixtures/mermaid/fail/architecture-bad-edge.mmd"), svg)
assert ok and de.is_error_render(svg.read_text()), "mmdc no longer false-succeeds here, or the detector missed it"
PY
rm -rf "$out"
[ $rc -eq 0 ] && echo "export self-test OK" || echo "export self-test FAILED"; exit $rc
