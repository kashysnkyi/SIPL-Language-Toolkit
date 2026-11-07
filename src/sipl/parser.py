"""Lark-based SIPL parser that produces a typed AST."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedInput

from . import ast


@dataclass(slots=True)
class SiplSyntaxError(Exception):
    message: str
    line: int
    column: int
    context: str = ""

    def __str__(self) -> str:
        suffix = f"\n{self.context}" if self.context else ""
        return f"{self.message} at {self.line}:{self.column}{suffix}"


@dataclass(frozen=True, slots=True)
class ParseResult:
    source: str
    parse_tree: Tree
    program: ast.Program


def _span(meta: Any) -> ast.SourceSpan:
    return ast.SourceSpan(
        line=meta.line,
        column=meta.column,
        end_line=meta.end_line,
        end_column=meta.end_column,
        start_pos=meta.start_pos,
        end_pos=meta.end_pos,
    )


class _AstBuilder:
    _binary = {
        "add": "+",
        "sub": "-",
        "mul": "*",
        "div": "div",
        "mod": "mod",
    }
    _boolean = {"bool_and": "and", "bool_or": "or"}

    def build(self, node: Tree | Token):
        if isinstance(node, Token):
            return str(node)

        name = str(node.data)
        children = node.children
        span = _span(node.meta)

        if name == "start":
            return self.build(children[0])
        if name == "program":
            statements = self.build(children[0]) if children else []
            body = ast.Block(span=span, statements=tuple(statements))
            return ast.Program(span=span, body=body)
        if name == "stmt_list":
            return [self.build(child) for child in children]
        if name == "block":
            statements = self.build(children[0]) if children else []
            return ast.Block(span=span, statements=tuple(statements))
        if name == "assignment":
            return ast.Assignment(
                span=span,
                name=str(children[0]),
                expression=self.build(children[1]),
            )
        if name == "skip_stmt":
            return ast.Skip(span=span)
        if name == "if_stmt":
            return ast.If(
                span=span,
                condition=self.build(children[0]),
                then_branch=self.build(children[1]),
                else_branch=self.build(children[2]),
            )
        if name == "while_stmt":
            return ast.While(
                span=span,
                condition=self.build(children[0]),
                body=self.build(children[1]),
            )
        if name == "number":
            return ast.Number(span=span, value=int(str(children[0])))
        if name == "variable":
            return ast.Variable(span=span, name=str(children[0]))
        if name in self._binary:
            return ast.BinaryExpr(
                span=span,
                operator=self._binary[name],
                left=self.build(children[0]),
                right=self.build(children[1]),
            )
        if name == "neg":
            return ast.UnaryExpr(span=span, operator="-", operand=self.build(children[0]))
        if name == "comparison":
            return ast.Comparison(
                span=span,
                operator=str(children[1]),
                left=self.build(children[0]),
                right=self.build(children[2]),
            )
        if name in self._boolean:
            return ast.BoolBinary(
                span=span,
                operator=self._boolean[name],
                left=self.build(children[0]),
                right=self.build(children[1]),
            )
        if name == "bool_not":
            return ast.UnaryExpr(span=span, operator="not", operand=self.build(children[0]))
        if name == "true_literal":
            return ast.BoolLiteral(span=span, value=True)
        if name == "false_literal":
            return ast.BoolLiteral(span=span, value=False)
        raise ValueError(f"Unsupported parse-tree node: {name}")


class SiplParser:
    def __init__(self) -> None:
        grammar = files("sipl.grammar").joinpath("sipl.lark").read_text(encoding="utf-8")
        self._parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=False,
        )

    def parse(self, source: str) -> ParseResult:
        try:
            tree = self._parser.parse(source)
        except UnexpectedInput as exc:
            expected = sorted(getattr(exc, "expected", []) or [])
            detail = f"; expected: {', '.join(expected)}" if expected else ""
            raise SiplSyntaxError(
                message=f"SIPL syntax error{detail}",
                line=exc.line,
                column=exc.column,
                context=exc.get_context(source, span=50),
            ) from exc
        program = _AstBuilder().build(tree)
        if not isinstance(program, ast.Program):
            raise TypeError("Parser did not produce Program")
        return ParseResult(source=source, parse_tree=tree, program=program)

