"""Tests of the diagram pane's helpers on the REAL files (DSKI-18, DEC-221 (a1)).

The plugin tests in hooks/register.test.tsx answer `process.run` with a stub, so they prove
what the mod does with a helper's answer. These prove the answers themselves:

- validate/validate.mjs, the strict syntax gate: refuses the repository's malformed fixtures with
  mermaid's own message when jsdom resolves, and says "validated: false" when it does not;
- renderer/render.mjs started the way the mod starts it (PES10_STDIN=1), from a plugin path that
  holds a space, a # and a %, where its own entry-point test would otherwise print nothing;
- the HTML page the "Open diagram" button writes, built around the SHIPPED renderer/vendor/mermaid.min.js.

Node 24 imports hooks/page.ts directly (it strips the types), which is what CI runs.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "mermaid" / "fail"
NODE = shutil.which("node")
JSDOM = ROOT / "skills" / "diagram-review" / "scripts" / "node_modules" / "jsdom"

needs_node = pytest.mark.skipif(NODE is None, reason="node is not on PATH")
needs_jsdom = pytest.mark.skipif(
    not JSDOM.exists(), reason="run `npm ci --prefix skills/diagram-review/scripts` first (CI does)"
)


def run_node(args, stdin="", env=None, cwd=None):
    import os

    full_env = {**os.environ, **(env or {})}
    done = subprocess.run(
        [NODE, *args], input=stdin, capture_output=True, text=True, env=full_env, cwd=cwd, timeout=60
    )
    assert done.returncode == 0, done.stderr
    return done.stdout


def validate(source, root=None):
    env = {"DIAGRAM_VALIDATE_ROOT": str(root)} if root is not None else None
    return json.loads(run_node([str(ROOT / "validate" / "validate.mjs")], stdin=source, env=env))


@needs_node
@needs_jsdom
class TestStrictGate:
    def test_refuses_the_malformed_fixtures_in_mermaids_own_words(self):
        names = ["class-unclosed-brace.mmd", "flowchart-missing-arrow.mmd"]
        assert all((FIXTURES / n).exists() for n in names)  # a positive control: the fixtures are there
        for name in names:
            out = validate((FIXTURES / name).read_text())
            assert out["ok"] is False and out["reason"] == "syntax", name
            assert "Parse error" in out["message"], name

    def test_accepts_a_valid_source_as_validated(self):
        out = validate("flowchart TD\n  A --> B\n")
        assert out["ok"] is True and out["validated"] is True

    def test_text_that_is_not_mermaid_is_refused(self):
        out = validate("hello world")
        assert out["ok"] is False and out["reason"] == "syntax"


@needs_node
class TestWithoutJsdom:
    def test_says_validated_false_and_refuses_nothing(self, tmp_path):
        for name in ["class-unclosed-brace.mmd", "flowchart-missing-arrow.mmd"]:
            out = validate((FIXTURES / name).read_text(), root=tmp_path)
            assert out == {"ok": True, "validated": False, "reason": "no-jsdom"}, name


@needs_node
class TestRendererFromAnAwkwardPath:
    SRC = "flowchart TD\n  A --> B\n"

    def test_a_space_a_hash_and_a_percent_break_the_helpers_entry_test_without_the_env(self, tmp_path):
        awkward = tmp_path / "sp ace#1%"
        shutil.copytree(ROOT / "renderer", awkward / "renderer")
        helper = str(awkward / "renderer" / "render.mjs")
        # without the variable the helper prints nothing (the bug the review found) ...
        assert run_node([helper], stdin=self.SRC) == ""
        # ... and with it, as the mod starts it, the helper answers
        out = json.loads(run_node([helper], stdin=self.SRC, env={"PES10_STDIN": "1"}))
        assert out["ok"] is True and out["kind"] == "flowchart" and "A" in out["unicode"]

    def test_the_mod_passes_the_variable(self):
        assert "env: { PES10_STDIN: '1' }" in (ROOT / "hooks" / "register.tsx").read_text()


@needs_node
class TestShippedPage:
    """The real guarantee: whatever the 3.5 MB bundle contains, the page forbids every network request."""

    BUNDLE = (ROOT / "renderer" / "vendor" / "mermaid.min.js").read_text()

    def build(self, source):
        script = (
            "import { htmlPage } from %s;"
            "import { readFileSync } from 'node:fs';"
            "const js = readFileSync(%s, 'utf8');"
            "process.stdout.write(htmlPage(%s, js, 'T <title>'))"
            % (
                json.dumps((ROOT / "hooks" / "page.ts").as_uri()),
                json.dumps(str(ROOT / "renderer" / "vendor" / "mermaid.min.js")),
                json.dumps(source),
            )
        )
        return run_node(["--input-type=module", "-e", script])

    @staticmethod
    def markup(html):
        """The page with every <script> body removed: what a browser parses as the document."""
        return re.sub(r"<script[^>]*>.*?</script>", "<script></script>", html, flags=re.S)

    def test_the_bundle_does_contain_url_strings_so_the_csp_is_what_matters(self):
        assert len(re.findall(r"https?://", self.BUNDLE)) > 50  # a positive control: 81 at 11.17.2

    def test_csp_forbids_everything_and_comes_before_any_script(self):
        html = self.build("flowchart TD\n  A --> B")
        meta = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', html)
        assert meta is not None
        csp = meta.group(1)
        assert "default-src 'none'" in csp  # covers connect, frame, object, media, worker, manifest
        assert "connect-src" not in csp and "frame-src" not in csp and "unsafe-eval" not in csp
        assert not re.search(r"https?:|\*", csp)
        assert html.index("Content-Security-Policy") < html.index("<script")

    def test_no_external_reference_in_the_markup(self):
        markup = self.markup(self.build("flowchart TD\n  A --> B"))
        assert len(re.findall(r"<script", markup)) == 2  # the bundle and the call, both inline
        assert not re.search(r"<script[^>]*\ssrc=", markup)
        assert not re.search(r"<(link|iframe|frame|object|embed|form|base|img|audio|video|source)\b", markup, re.I)
        assert not re.search(r"https?://", markup)

    def test_a_source_cannot_break_out_of_the_page(self):
        evil = "flowchart TD\n  A[</script><img src=https://evil.example/x onerror=alert(1)>] --> B"
        html = self.build(evil)
        markup = self.markup(html)
        assert "evil.example" not in markup
        assert not re.search(r"<img\b", markup, re.I)
        assert "</script><img" not in html
        # the title is escaped too
        assert "<title>T &lt;title&gt;</title>" in html
