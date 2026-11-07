import json

import pytest

from sipl.cli import main


@pytest.fixture
def source_file(tmp_path):
    path = tmp_path / "program.sipl"
    path.write_text("begin X := X + 1 end", encoding="utf-8")
    return path


def test_check_and_parse_json(source_file, capsys):
    assert main(["check", str(source_file)]) == 0
    assert "OK:" in capsys.readouterr().out

    assert main(["parse", str(source_file), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema_version"] == "1.0"
    assert data["ast"]["kind"] == "Program"


def test_run_and_trace_modes(source_file, capsys):
    assert main(["run", str(source_file), "--state", "X=4"]) == 0
    assert "X=5" in capsys.readouterr().out

    assert main(["trace", str(source_file), "--state", "X=4", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["state"] == {"X": 5}
    assert any(event["kind"] == "VariableChanged" for event in data["events"])


def test_semantic_tree_ast_compare_and_output(source_file, tmp_path, capsys):
    assert main(["semantic", str(source_file)]) == 0
    assert "AS^X" in capsys.readouterr().out

    tree_dot = tmp_path / "tree.dot"
    assert main(["tree", str(source_file), "--format", "dot", "--output", str(tree_dot)]) == 0
    assert tree_dot.read_text(encoding="utf-8").startswith("digraph SIPL")

    assert main(["tree", str(source_file), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["tree"]["kind"] == "Rule"

    assert main(["ast", str(source_file), "--format", "text"]) == 0
    assert "Program" in capsys.readouterr().out

    assert main(["ast", str(source_file), "--format", "dot"]) == 0
    assert "digraph SIPL" in capsys.readouterr().out

    assert main(["compare", str(source_file), "--json"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["parse_tree_nodes"] > summary["ast_nodes"]


def test_cli_syntax_runtime_and_state_errors(tmp_path, capsys):
    bad = tmp_path / "bad.sipl"
    bad.write_text("begin X = 1 end", encoding="utf-8")
    assert main(["check", str(bad), "--json"]) == 2
    assert json.loads(capsys.readouterr().err)["error"]["type"] == "syntax"

    runtime = tmp_path / "runtime.sipl"
    runtime.write_text("begin X := Y end", encoding="utf-8")
    assert main(["run", str(runtime), "--json"]) == 3
    assert json.loads(capsys.readouterr().err)["error"]["type"] == "runtime"

    assert main(["run", str(runtime), "--state", "broken"]) == 3
    assert "NAME=INTEGER" in capsys.readouterr().err


def test_missing_file_reports_io_error(capsys):
    assert main(["check", "definitely-missing.sipl"]) == 2
    assert "I/O error" in capsys.readouterr().err

