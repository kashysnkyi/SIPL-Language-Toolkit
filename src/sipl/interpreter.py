"""Executable SIPL semantics with observable trace events."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from . import ast


@dataclass(slots=True)
class SiplRuntimeError(Exception):
    message: str
    span: ast.SourceSpan | None = None

    def __str__(self) -> str:
        location = f" at {self.span.short()}" if self.span else ""
        return f"{self.message}{location}"


class StepLimitExceeded(SiplRuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TraceEvent:
    kind: str
    span: ast.SourceSpan
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "span": asdict(self.span), "payload": self.payload}


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    state: dict[str, int]
    events: tuple[TraceEvent, ...]
    steps: int


class Interpreter:
    def __init__(self, step_limit: int = 10_000) -> None:
        if step_limit <= 0:
            raise ValueError("step_limit must be positive")
        self.step_limit = step_limit
        self._steps = 0
        self._events: list[TraceEvent] = []
        self._state: dict[str, int] = {}

    def run(self, program: ast.Program, state: dict[str, int] | None = None) -> ExecutionResult:
        self._steps = 0
        self._events = []
        self._state = dict(state or {})
        self._exec(program.body)
        self._emit("ProgramFinished", program.span, state=dict(self._state), steps=self._steps)
        return ExecutionResult(
            state=dict(self._state),
            events=tuple(self._events),
            steps=self._steps,
        )

    def _emit(self, kind: str, span: ast.SourceSpan, **payload: Any) -> None:
        self._events.append(TraceEvent(kind=kind, span=span, payload=payload))

    def _tick(self, span: ast.SourceSpan) -> None:
        self._steps += 1
        if self._steps > self.step_limit:
            raise StepLimitExceeded(
                f"Step limit {self.step_limit} exceeded; possible infinite loop",
                span,
            )

    def _exec(self, statement: ast.Statement) -> None:
        self._tick(statement.span)
        self._emit("BeforeStatement", statement.span, statement=type(statement).__name__)

        if isinstance(statement, ast.Block):
            for child in statement.statements:
                self._exec(child)
        elif isinstance(statement, ast.Assignment):
            value = self._eval(statement.expression)
            old_value = self._state.get(statement.name)
            self._state[statement.name] = value
            self._emit(
                "VariableChanged",
                statement.span,
                name=statement.name,
                old=old_value,
                new=value,
            )
        elif isinstance(statement, ast.Skip):
            pass
        elif isinstance(statement, ast.If):
            value = self._truth(self._eval(statement.condition))
            self._emit("ConditionEvaluated", statement.condition.span, value=value, owner="if")
            self._exec(statement.then_branch if value else statement.else_branch)
        elif isinstance(statement, ast.While):
            iteration = 0
            while True:
                self._tick(statement.span)
                value = self._truth(self._eval(statement.condition))
                self._emit(
                    "ConditionEvaluated",
                    statement.condition.span,
                    value=value,
                    owner="while",
                    iteration=iteration,
                )
                if not value:
                    break
                self._exec(statement.body)
                iteration += 1
        else:
            raise SiplRuntimeError(f"Unsupported statement {type(statement).__name__}", statement.span)

        self._emit("AfterStatement", statement.span, statement=type(statement).__name__)

    @staticmethod
    def _truth(value: int | bool) -> bool:
        return bool(value)

    def _eval(self, expression: ast.Expr) -> int | bool:
        if isinstance(expression, ast.Number):
            return expression.value
        if isinstance(expression, ast.BoolLiteral):
            return expression.value
        if isinstance(expression, ast.Variable):
            if expression.name not in self._state:
                raise SiplRuntimeError(f"Undefined variable '{expression.name}'", expression.span)
            return self._state[expression.name]
        if isinstance(expression, ast.UnaryExpr):
            value = self._eval(expression.operand)
            if expression.operator == "-":
                return -int(value)
            if expression.operator == "not":
                return not self._truth(value)
        if isinstance(expression, ast.BinaryExpr):
            left = int(self._eval(expression.left))
            right = int(self._eval(expression.right))
            operations: dict[str, Callable[[int, int], int]] = {
                "+": lambda a, b: a + b,
                "-": lambda a, b: a - b,
                "*": lambda a, b: a * b,
            }
            if expression.operator in operations:
                return operations[expression.operator](left, right)
            if expression.operator in {"div", "mod"}:
                if right == 0:
                    raise SiplRuntimeError("Division by zero", expression.span)
                quotient = int(left / right)
                return quotient if expression.operator == "div" else left - quotient * right
        if isinstance(expression, ast.Comparison):
            left = self._eval(expression.left)
            right = self._eval(expression.right)
            comparisons = {
                "=": lambda a, b: a == b,
                "!=": lambda a, b: a != b,
                "<": lambda a, b: a < b,
                "<=": lambda a, b: a <= b,
                ">": lambda a, b: a > b,
                ">=": lambda a, b: a >= b,
            }
            return comparisons[expression.operator](left, right)
        if isinstance(expression, ast.BoolBinary):
            if expression.operator == "and":
                return self._truth(self._eval(expression.left)) and self._truth(
                    self._eval(expression.right)
                )
            if expression.operator == "or":
                return self._truth(self._eval(expression.left)) or self._truth(
                    self._eval(expression.right)
                )
        raise SiplRuntimeError(f"Unsupported expression {type(expression).__name__}", expression.span)

