"""Text, JSON and Graphviz DOT renderers for parse trees and AST."""

from __future__ import annotations

import json
from dataclasses import fields
from typing import Any, Iterable

from lark import Token, Tree

from . import ast


def _tree_span(tree: Tree) -> dict[str, int]:
    meta = tree.meta
    return {
        "line": meta.line,
        "column": meta.column,
        "end_line": meta.end_line,
        "end_column": meta.end_column,
        "start_pos": meta.start_pos,
        "end_pos": meta.end_pos,
    }


def parse_tree_to_dict(node: Tree | Token) -> dict[str, Any]:
    if isinstance(node, Token):
        return {
            "kind": "Token",
            "type": node.type,
            "value": str(node),
            "span": {
                "line": node.line,
                "column": node.column,
                "end_line": node.end_line,
                "end_column": node.end_column,
                "start_pos": node.start_pos,
                "end_pos": node.end_pos,
            },
        }
    return {
        "kind": "Rule",
        "name": str(node.data),
        "span": _tree_span(node),
        "children": [parse_tree_to_dict(child) for child in node.children],
    }


def parse_tree_text(node: Tree | Token, prefix: str = "", last: bool = True) -> str:
    connector = "└─ " if last else "├─ "
    if isinstance(node, Token):
        label = f"{node.type}: {node!s} [{node.line}:{node.column}]"
        return prefix + connector + label
    label = f"{node.data} [{node.meta.line}:{node.meta.column}-{node.meta.end_line}:{node.meta.end_column}]"
    lines = [prefix + connector + label]
    child_prefix = prefix + ("   " if last else "│  ")
    for index, child in enumerate(node.children):
        lines.append(parse_tree_text(child, child_prefix, index == len(node.children) - 1))
    return "\n".join(lines)


def ast_text(node: ast.Node, prefix: str = "", last: bool = True) -> str:
    connector = "└─ " if last else "├─ "
    attributes: list[str] = []
    children: list[ast.Node] = []
    for field in fields(node):
        if field.name == "span":
            continue
        value = getattr(node, field.name)
        if isinstance(value, ast.Node):
            children.append(value)
        elif isinstance(value, tuple) and all(isinstance(item, ast.Node) for item in value):
            children.extend(value)
        else:
            attributes.append(f"{field.name}={value!r}")
    suffix = f" ({', '.join(attributes)})" if attributes else ""
    lines = [prefix + connector + f"{type(node).__name__}{suffix} [{node.span.short()}]"]
    child_prefix = prefix + ("   " if last else "│  ")
    for index, child in enumerate(children):
        lines.append(ast_text(child, child_prefix, index == len(children) - 1))
    return "\n".join(lines)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _dot(nodes: Iterable[tuple[str, str, str | None]]) -> str:
    lines = ["digraph SIPL {", "  rankdir=TB;", '  node [shape=box, fontname="Arial"];']
    for node_id, label, parent in nodes:
        lines.append(f'  {node_id} [label="{_escape(label)}"];')
        if parent is not None:
            lines.append(f"  {parent} -> {node_id};")
    lines.append("}")
    return "\n".join(lines)


def parse_tree_dot(root: Tree) -> str:
    rows: list[tuple[str, str, str | None]] = []
    counter = 0

    def visit(node: Tree | Token, parent: str | None = None) -> None:
        nonlocal counter
        node_id = f"n{counter}"
        counter += 1
        if isinstance(node, Token):
            label = f"{node.type}: {node}\\n{node.line}:{node.column}"
            rows.append((node_id, label, parent))
        else:
            label = f"{node.data}\\n{node.meta.line}:{node.meta.column}"
            rows.append((node_id, label, parent))
            for child in node.children:
                visit(child, node_id)

    visit(root)
    return _dot(rows)


def ast_dot(root: ast.Node) -> str:
    rows: list[tuple[str, str, str | None]] = []
    counter = 0

    def visit(node: ast.Node, parent: str | None = None) -> None:
        nonlocal counter
        node_id = f"n{counter}"
        counter += 1
        rows.append((node_id, f"{type(node).__name__}\\n{node.span.short()}", parent))
        for field in fields(node):
            value = getattr(node, field.name)
            if isinstance(value, ast.Node):
                visit(value, node_id)
            elif isinstance(value, tuple):
                for item in value:
                    if isinstance(item, ast.Node):
                        visit(item, node_id)

    visit(root)
    return _dot(rows)


def comparison_summary(parse_tree: Tree, program: ast.Program) -> dict[str, Any]:
    def count_tree(node: Tree | Token) -> int:
        return 1 + (sum(count_tree(child) for child in node.children) if isinstance(node, Tree) else 0)

    parse_nodes = count_tree(parse_tree)
    ast_nodes = sum(1 for _ in ast.walk(program))
    return {
        "parse_tree_nodes": parse_nodes,
        "ast_nodes": ast_nodes,
        "removed_concrete_nodes": parse_nodes - ast_nodes,
        "explanation": (
            "Parse tree preserves grammar rules and tokens; AST keeps only semantic constructs "
            "and attaches SourceSpan to each node."
        ),
    }


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)

