"""diagram_truth.py: traced nodes pass, untraced or unresolvable ones fail, Quest edges must match exactly."""
import json

import diagram_truth as dt


def run(tmp_path, body, snapshot=None, name="doc.mmd"):
    (tmp_path / name).write_text(body)
    args = ["--root", str(tmp_path), "--json", str(tmp_path / name)]
    if snapshot is not None:
        (tmp_path / "snap.json").write_text(json.dumps({"data": snapshot}))
        args += ["--quest-snapshot", str(tmp_path / "snap.json")]
    return args


def result(capsys, args):
    code = dt.main(args)
    return code, json.loads(capsys.readouterr().out)


def rules(out):
    return sorted({f["rule"] for f in out["findings"] if f["severity"] == "error"})


BASE = 'flowchart LR\n  accTitle: t\n  accDescr: d\n  api["API"] --> db[("DB")]\n'


def test_traced_nodes_pass(tmp_path, capsys):
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "schema.sql").write_text("CREATE TABLE orders (id int);")
    body = BASE + "  %% ref api = path:services/api\n  %% ref db = schema:schema.sql#orders\n"
    code, out = result(capsys, run(tmp_path, body))
    assert code == 0 and out["errors"] == 0


def test_untraced_and_unresolved_fail(tmp_path, capsys):
    body = BASE + "  %% ref api = path:services/missing\n"
    code, out = result(capsys, run(tmp_path, body))
    assert code == 1 and rules(out) == ["unresolved", "untraced"]


def test_symbol_must_appear_in_file(tmp_path, capsys):
    (tmp_path / "app.py").write_text("def place_order():\n    pass\n")
    body = BASE + "  %% ref api = path:app.py#refund_order\n  %% ref db = ext:Managed database\n"
    code, out = result(capsys, run(tmp_path, body))
    assert code == 1 and rules(out) == ["unresolved"]


def test_ext_is_listed_not_failed_and_orphans_warn(tmp_path, capsys):
    body = BASE + "  %% ref api = ext:Partner API\n  %% ref db = ext:Their database\n  %% ref ghost = ext:Nothing\n"
    code, out = result(capsys, run(tmp_path, body))
    sev = {(f["rule"], f["severity"]) for f in out["findings"]}
    assert code == 0 and ("external", "info") in sev and ("orphan-ref", "warning") in sev


def test_quest_edges_must_match_dependencies(tmp_path, capsys):
    snap = [{"id": "T-1", "dependencies": []}, {"id": "T-2", "dependencies": ["T-1"]}, {"id": "T-3", "dependencies": ["T-1"]}]
    head = "flowchart LR\n  accTitle: t\n  accDescr: d\n  %% edges: quest-dependencies\n"
    refs = "  %% ref T_1 = quest:T-1\n  %% ref T_2 = quest:T-2\n  %% ref T_3 = quest:T-3\n"
    good = head + "  T_1 --> T_2\n  T_1 --> T_3\n" + refs
    code, out = result(capsys, run(tmp_path, good, snap))
    assert code == 0, out
    bad = head + "  T_1 --> T_2\n  T_2 --> T_3\n" + refs
    code, out = result(capsys, run(tmp_path, bad, snap))
    assert code == 1 and rules(out) == ["edge-missing", "edge-not-in-source"]


def test_unknown_quest_id_fails(tmp_path, capsys):
    body = 'flowchart LR\n  accTitle: t\n  accDescr: d\n  T_9["Nine"]\n  %% ref T_9 = quest:T-9\n'
    code, out = result(capsys, run(tmp_path, body, [{"id": "T-1"}]))
    assert code == 1 and rules(out) == ["unresolved"]
