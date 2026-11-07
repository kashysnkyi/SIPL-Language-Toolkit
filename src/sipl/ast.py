"""Typed abstract syntax tree for SIPL."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SourceSpan:
    line: int
    column: int
    end_line: int
    end_column: int
    start_pos: int
    end_pos: int

    def short(self) -> str:
        return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"


@dataclass(frozen=True, slots=True)
class Node:
    span: SourceSpan


class Expr(Node):
    pass


@dataclass(frozen=True, slots=True)
class Number(Expr):
    value: int


@dataclass(frozen=True, slots=True)
class Variable(Expr):
    name: str


@dataclass(frozen=True, slots=True)
class UnaryExpr(Expr):
    operator: str
    operand: Expr


@dataclass(frozen=True, slots=True)
class BinaryExpr(Expr):
    operator: str
    left: Expr
    right: Expr


@dataclass(frozen=True, slots=True)
class BoolLiteral(Expr):
    value: bool


@dataclass(frozen=True, slots=True)
class Comparison(Expr):
    operator: str
    left: Expr
    right: Expr


@dataclass(frozen=True, slots=True)
class BoolBinary(Expr):
    operator: str
    left: Expr
    right: Expr


class Statement(Node):
    pass


@dataclass(frozen=True, slots=True)
class Assignment(Statement):
    name: str
    expression: Expr


@dataclass(frozen=True, slots=True)
class Skip(Statement):
    pass


@dataclass(frozen=True, slots=True)
class If(Statement):
    condition: Expr
    then_branch: Statement
    else_branch: Statement


@dataclass(frozen=True, slots=True)
class While(Statement):
    condition: Expr
    body: Statement


@dataclass(frozen=True, slots=True)
class Block(Statement):
    statements: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class Program(Node):
    body: Block


def node_to_dict(value: Any) -> Any:
    """Convert AST objects to a stable JSON-compatible representation."""
    if isinstance(value, SourceSpan):
        return asdict(value)
    if isinstance(value, tuple):
        return [node_to_dict(item) for item in value]
    if isinstance(value, list):
        return [node_to_dict(item) for item in value]
    if is_dataclass(value):
        result: dict[str, Any] = {"kind": type(value).__name__}
        for field in fields(value):
            result[field.name] = node_to_dict(getattr(value, field.name))
        return result
    return value


def walk(node: Node):
    """Yield an AST node and all of its descendant nodes."""
    yield node
    for field in fields(node):
        value = getattr(node, field.name)
        if isinstance(value, Node):
            yield from walk(value)
        elif isinstance(value, tuple):
            for item in value:
                if isinstance(item, Node):
                    yield from walk(item)

