"""diagram_export.py stays opt-in and owns only its own cache. No install needed."""
import diagram_export as de


def test_install_without_yes_installs_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DIAGRAM_SKILLS_CACHE", str(tmp_path / "c"))
    assert de.main(["install"]) == 3
    assert "650 MB" in capsys.readouterr().out
    assert not (tmp_path / "c").exists()


def test_export_without_install_exits_2(tmp_path, monkeypatch):
    monkeypatch.setenv("DIAGRAM_SKILLS_CACHE", str(tmp_path / "c"))
    doc = tmp_path / "d.md"
    doc.write_text("x\n\n```mermaid\nflowchart LR\n  a --> b\n```\n")
    assert de.main(["export", str(doc)]) == 2


def test_uninstall_removes_only_its_own_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("DIAGRAM_SKILLS_CACHE", str(tmp_path / "c"))
    foreign = tmp_path / "c" / "mmdc"
    foreign.mkdir(parents=True)
    (foreign / "keep.txt").write_text("not ours")
    assert de.main(["uninstall"]) == 2 and (foreign / "keep.txt").exists()
    (foreign / de.MARKER).write_text("ours")
    assert de.main(["uninstall"]) == 0 and not foreign.exists()
    assert (tmp_path / "c").exists()


def test_error_render_detection():
    assert de.is_error_render('<svg aria-roledescription="error"><text>Syntax error in text</text></svg>')
    assert not de.is_error_render('<svg aria-roledescription="flowchart-v2"><g>ok</g></svg>')


def test_renderer_pin_matches_parse_check():
    assert de.parse_pin() == "11.17.2"
