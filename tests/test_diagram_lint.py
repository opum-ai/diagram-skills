"""diagram_lint.py: every rule fires on a bad diagram and stays quiet on a good one."""
import json
import textwrap

import diagram_lint as dl

GOOD_BODY = """\
flowchart LR
  accTitle: Order flow
  accDescr: An order is placed, paid and shipped.
  placed["Order placed"] -- "pay" --> paid["Paid"]
  paid -- "ship" --> shipped["Shipped"]
"""
EXPLANATION = (
    "Read it left to right. A customer places an order, the payment step marks it paid, "
    "and the warehouse ships it. Nothing ships before payment clears."
)


def doc(body: str, before: str = "How does an order move?", after: str = EXPLANATION) -> str:
    return f"# Orders\n\n{before}\n\n```mermaid\n{body}```\n\n{after}\n"


def run(tmp_path, text, name="doc.md", level=dl.DEFAULT_LEVEL):
    p = tmp_path / name
    p.write_text(textwrap.dedent(text))
    findings = []
    for d in dl.diagrams_in(p):
        findings += dl.lint(d, level)
    return findings


def rules(findings, severity="error"):
    return sorted({f.rule for f in findings if f.severity == severity})


def test_good_diagram_has_no_findings(tmp_path):
    assert run(tmp_path, doc(GOOD_BODY)) == []


def test_missing_accessibility_fields(tmp_path):
    body = GOOD_BODY.replace("  accTitle: Order flow\n", "").replace("  accDescr: An order is placed, paid and shipped.\n", "")
    assert rules(run(tmp_path, doc(body))) == ["a11y-descr", "a11y-title"]


def test_accdescr_block_form_counts(tmp_path):
    body = GOOD_BODY.replace("  accDescr: An order is placed, paid and shipped.\n", "  accDescr {\n    Placed, paid, shipped.\n  }\n")
    assert run(tmp_path, doc(body)) == []


def test_unquoted_node_label(tmp_path):
    body = GOOD_BODY.replace('shipped["Shipped"]', "shipped[Shipped (UPS)]")
    assert "quote-label" in rules(run(tmp_path, doc(body)))


def test_unquoted_edge_label(tmp_path):
    body = GOOD_BODY.replace('-- "ship" -->', "-->|ship|")
    assert "quote-label" in rules(run(tmp_path, doc(body)))


def test_lowercase_end_id(tmp_path):
    body = GOOD_BODY + '  shipped --> end["Done"]\n'
    assert "banned-id" in rules(run(tmp_path, doc(body)))


def test_o_or_x_id_glued_to_arrow(tmp_path):
    body = GOOD_BODY + "  shipped-->xray\n"
    assert "banned-id" in rules(run(tmp_path, doc(body)))


def test_spaced_o_id_is_fine(tmp_path):
    body = GOOD_BODY + '  shipped --> orders["Orders"]\n'
    assert run(tmp_path, doc(body)) == []


def chain(n: int) -> str:
    lines = ["flowchart LR", "  accTitle: Chain", "  accDescr: A chain of steps."]
    lines += [f'  s{i}["Step {i}"] --> s{i + 1}["Step {i + 1}"]' for i in range(n - 1)]
    return "\n".join(lines) + "\n"


def test_node_cap_by_level(tmp_path):
    assert rules(run(tmp_path, doc(chain(8)), level="beginner")) == ["node-cap"]
    assert run(tmp_path, doc(chain(8)), level="intermediate") == []
    assert rules(run(tmp_path, doc(chain(21)), level="advanced")) == ["node-cap"]


def test_fence_level_comment_overrides_default(tmp_path):
    body = chain(10).replace("flowchart LR\n", "flowchart LR\n  %% level: beginner\n")
    assert rules(run(tmp_path, doc(body), level="advanced")) == ["node-cap"]


def test_classdef_needs_legend(tmp_path):
    body = GOOD_BODY + "  classDef done stroke-width:3px\n  class shipped done\n"
    assert rules(run(tmp_path, doc(body))) == ["legend"]
    assert run(tmp_path, doc(body, after=EXPLANATION + " Legend: a thick border marks the final state.")) == []


def test_explanation_required_after_fence(tmp_path):
    assert rules(run(tmp_path, doc(GOOD_BODY, after="Done."))) == ["explanation"]


def test_lead_sentence_is_a_warning(tmp_path):
    findings = run(tmp_path, doc(GOOD_BODY, before=""))
    assert rules(findings) == [] and rules(findings, "warning") == ["lead-sentence"]


def test_off_profile_types_and_shapes(tmp_path):
    assert "profile-type" in rules(run(tmp_path, doc(GOOD_BODY.replace("flowchart LR", "graph LR"))))
    assert "profile-type" in rules(run(tmp_path, doc(GOOD_BODY.replace("flowchart LR", "mindmap"))))
    body = GOOD_BODY + '  x1@{ shape: rounded, label: "Refund" }\n'
    assert "profile-shape" in rules(run(tmp_path, doc(body)))


def test_non_mermaid_fences_are_ignored(tmp_path):
    text = "# T\n\n```text\nflowchart LR\n  a[bad (label)]\n```\n\n```mermaid-broken\ngraph\n```\n"
    assert run(tmp_path, text) == []


def test_mmd_files_skip_prose_rules(tmp_path):
    assert run(tmp_path, GOOD_BODY, name="flow.mmd") == []


def test_node_counts_per_type():
    seq = "sequenceDiagram\n  accTitle: t\n  accDescr: d\n  participant U as User\n  U->>API: GET /docs\n  API-->>DB: query\n  DB-->>API: rows\n"
    state = "stateDiagram-v2\n  accTitle: t\n  accDescr: d\n  [*] --> Draft\n  Draft --> Review : submit\n  Review --> Done : approve\n  Done --> [*]\n"
    er = 'erDiagram\n  accTitle: t\n  accDescr: d\n  CUSTOMER ||--o{ ORDER : places\n  ORDER ||--|{ LINE_ITEM : contains\n  PRODUCT {\n    string sku\n  }\n'
    cls = "classDiagram\n  accTitle: t\n  accDescr: d\n  class Animal\n  Animal <|-- Dog\n  Animal <|-- Cat\n"
    assert dl.nodes_of(seq) == {"U", "API", "DB"}
    assert dl.nodes_of(state) == {"Draft", "Review", "Done"}
    assert dl.nodes_of(er) == {"CUSTOMER", "ORDER", "LINE_ITEM", "PRODUCT"}
    assert dl.nodes_of(cls) == {"Animal", "Dog", "Cat"}
    assert dl.nodes_of(GOOD_BODY) == {"placed", "paid", "shipped"}


def test_subgraph_ids_are_not_nodes():
    body = 'flowchart LR\n  accTitle: t\n  accDescr: d\n  subgraph core["Core"]\n    a["A"] --> b["B"]\n  end\n'
    assert dl.nodes_of(body) == {"a", "b"}


def test_cli_exit_codes_and_json(tmp_path, capsys):
    good = tmp_path / "good.md"
    good.write_text(doc(GOOD_BODY))
    bad = tmp_path / "bad.md"
    bad.write_text(doc(GOOD_BODY.replace("flowchart LR", "graph LR")))
    assert dl.main([str(good)]) == 0
    capsys.readouterr()
    assert dl.main([str(bad), "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["errors"] >= 1 and out["findings"][0]["rule"] == "profile-type"
    assert dl.main([str(tmp_path / "missing.md")]) == 2
