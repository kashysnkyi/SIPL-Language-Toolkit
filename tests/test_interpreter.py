import pytest

from sipl.interpreter import Interpreter, SiplRuntimeError, StepLimitExceeded
from sipl.parser import SiplParser


def run(source, state=None, limit=10_000):
    program = SiplParser().parse(source).program
    return Interpreter(step_limit=limit).run(program, state)


def test_parity_program():
    source = """begin
      while N > 1 do N := N - 2;
      if N = 1 then R := 1 else R := 0
    end"""
    assert run(source, {"N": 5}).state == {"N": 1, "R": 1}
    assert run(source, {"N": 6}).state == {"N": 0, "R": 0}


def test_power_program_and_trace():
    source = """begin
      R := 1;
      while Y > 0 do begin R := R * X; Y := Y - 1 end
    end"""
    result = run(source, {"X": 2, "Y": 5})
    assert result.state == {"X": 2, "Y": 0, "R": 32}
    assert any(event.kind == "ConditionEvaluated" for event in result.events)
    changes = [e for e in result.events if e.kind == "VariableChanged" and e.payload["name"] == "R"]
    assert changes[-1].payload["new"] == 32
    assert result.events[-1].kind == "ProgramFinished"


def test_div_mod_and_truncation_to_zero():
    result = run("begin A := -17 div 5; B := -17 mod 5 end")
    assert result.state == {"A": -3, "B": -2}


def test_undefined_variable():
    with pytest.raises(SiplRuntimeError, match="Undefined variable"):
        run("begin X := Y + 1 end")


def test_division_by_zero():
    with pytest.raises(SiplRuntimeError, match="Division by zero"):
        run("begin X := 1 div 0 end")


def test_step_limit_stops_infinite_loop():
    with pytest.raises(StepLimitExceeded):
        run("begin while true do skip end", limit=20)


def test_short_circuit_boolean_logic():
    result = run("begin if false and X = 1 then Y := 1 else Y := 2 end")
    assert result.state == {"Y": 2}

