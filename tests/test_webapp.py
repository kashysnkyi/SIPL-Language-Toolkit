import pytest

from sipl.webapp import analyze_source, parse_state, run_source


def test_parse_state_from_text_and_mapping():
    assert parse_state("N=5, X=-2") == {"N": 5, "X": -2}
    assert parse_state({"R": "7"}) == {"R": 7}


def test_parse_state_rejects_invalid_item():
    with pytest.raises(ValueError, match="NAME=INTEGER"):
        parse_state("N")


def test_analyze_source_returns_ast_and_semantics():
    result = analyze_source("begin X := 1 end")

    assert result["ok"] is True
    assert result["ast"]["kind"] == "Program"
    assert "AS" in result["semantic_term"]
    assert result["comparison"]


def test_run_source_returns_state_and_trace():
    source = "begin while N > 1 do N := N - 2; if N = 1 then R := 1 else R := 0 end"
    result = run_source(source, "N=5")

    assert result["ok"] is True
    assert result["state"] == {"N": 1, "R": 1}
    assert result["steps"] > 0
    assert result["events"]
