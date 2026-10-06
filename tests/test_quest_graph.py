"""quest_graph.py emits profile-clean diagrams whose edges are Quest's dependencies."""
import json

import diagram_lint as dl
import diagram_truth as dt
import quest_graph as qg

TASKS = [
    {"id": "T-1", "title": "Stripe keys", "status": "Done", "dependencies": []},
    {"id": "T-2", "title": "Charge card", "status": "In Progress", "dependencies": ["T-1"]},
    {"id": "T-3", "title": "Refunds \"v1\"", "status": "To Do", "dependencies": ["T-2"]},
    {"id": "T-10", "title": "Launch", "status": "To Do", "dependencies": ["T-2", "T-3"]},
]


def lint_ok(mermaid):
    return [f for f in dl.lint(dl.Diagram(where="x", src=mermaid), "intermediate") if f.severity == "error"]


# ---- quest_graph

def test_quest_graph_edges_labels_and_order(tmp_path, capsys):
    (tmp_path / "t.json").write_text(json.dumps({"data": TASKS}))
    assert qg.main(["deps", "--input", str(tmp_path / "t.json")]) == 0
    out = capsys.readouterr().out
    assert out.index("T_2[") < out.index("T_10[")  # natural order, not text order
    assert dt.flow_edges(out) == {("T_1", "T_2"), ("T_2", "T_3"), ("T_2", "T_10"), ("T_3", "T_10")}
    assert "#quot;v1#quot;" in out and "(in progress)" in out
    assert lint_ok(out) == []


def test_quest_graph_open_filter_and_cap(tmp_path, capsys):
    (tmp_path / "t.json").write_text(json.dumps({"data": TASKS}))
    assert qg.main(["deps", "--open", "--input", str(tmp_path / "t.json")]) == 0
    assert "T_1[" not in capsys.readouterr().out
    many = [{"id": f"T-{i}", "title": "x", "status": "To Do", "dependencies": []} for i in range(9)]
    (tmp_path / "m.json").write_text(json.dumps({"data": many}))
    assert qg.main(["deps", "--level", "beginner", "--input", str(tmp_path / "m.json")]) == 3


def test_quest_graph_output_passes_truth_against_its_source(tmp_path, capsys):
    (tmp_path / "t.json").write_text(json.dumps({"data": TASKS}))
    qg.main(["deps", "--markdown", "--input", str(tmp_path / "t.json")])
    md = capsys.readouterr().out
    (tmp_path / "plan.md").write_text("Plan?\n\n" + md + "\nWords " * 25)
    assert dt.main(["--root", str(tmp_path), "--quest-snapshot", str(tmp_path / "t.json"), "--json", str(tmp_path / "plan.md")]) == 0
