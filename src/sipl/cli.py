"""Command-line interface for SIPL Language Toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import ast
from .interpreter import Interpreter, SiplRuntimeError
from .parser import SiplParser, SiplSyntaxError
from .semantics import semantic_term
from .visualization import (
    ast_dot,
    ast_text,
    comparison_summary,
    json_text,
    parse_tree_dot,
    parse_tree_text,
    parse_tree_to_dict,
)

SCHEMA_VERSION = "1.0"


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _state(values: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"State item must have NAME=INTEGER form: {item}")
        name, raw = item.split("=", 1)
        if not name.isidentifier():
            raise ValueError(f"Invalid variable name: {name}")
        result[name] = int(raw)
    return result


def _write(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8")
    else:
        print(text)


def _envelope(command: str, **payload: Any) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "command": command, **payload}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sipl", description="SIPL Language Toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Validate SIPL syntax")
    check.add_argument("file")
    check.add_argument("--json", action="store_true")

    parse = sub.add_parser("parse", help="Parse source and print typed AST")
    parse.add_argument("file")
    parse.add_argument("--json", action="store_true")

    for name in ("run", "trace"):
        command = sub.add_parser(name, help=f"{name.capitalize()} a SIPL program")
        command.add_argument("file")
        command.add_argument("--state", action="append", default=[], metavar="NAME=VALUE")
        command.add_argument("--step-limit", type=int, default=10_000)
        command.add_argument("--json", action="store_true")

    semantic = sub.add_parser("semantic", help="Build a course-style semantic term")
    semantic.add_argument("file")
    semantic.add_argument("--json", action="store_true")

    for name in ("tree", "ast"):
        command = sub.add_parser(name, help=f"Render {name}")
        command.add_argument("file")
        command.add_argument("--format", choices=("text", "json", "dot"), default="text")
        command.add_argument("--output")

    compare = sub.add_parser("compare", help="Compare parse tree and AST")
    compare.add_argument("file")
    compare.add_argument("--json", action="store_true")
    return parser


def execute(args: argparse.Namespace) -> int:
    source = _source(args.file)
    result = SiplParser().parse(source)

    if args.command == "check":
        payload = _envelope("check", ok=True, file=args.file)
        print(json_text(payload) if args.json else f"OK: {args.file}")
        return 0

    if args.command == "parse":
        data = ast.node_to_dict(result.program)
        print(json_text(_envelope("parse", ast=data)) if args.json else ast_text(result.program))
        return 0

    if args.command in {"run", "trace"}:
        initial = _state(args.state)
        execution = Interpreter(step_limit=args.step_limit).run(result.program, initial)
        payload = _envelope(
            args.command,
            state=execution.state,
            steps=execution.steps,
            events=[event.to_dict() for event in execution.events],
        )
        if args.json:
            print(json_text(payload))
        elif args.command == "run":
            print("Final state:", ", ".join(f"{k}={v}" for k, v in sorted(execution.state.items())))
            print(f"Steps: {execution.steps}")
        else:
            for index, event in enumerate(execution.events, 1):
                print(f"{index:03d} {event.kind:<20} {event.span.short()} {event.payload}")
        return 0

    if args.command == "semantic":
        term = semantic_term(result.program)
        print(json_text(_envelope("semantic", term=term)) if args.json else term)
        return 0

    if args.command == "tree":
        if args.format == "text":
            text = parse_tree_text(result.parse_tree)
        elif args.format == "json":
            text = json_text(_envelope("tree", tree=parse_tree_to_dict(result.parse_tree)))
        else:
            text = parse_tree_dot(result.parse_tree)
        _write(text, args.output)
        return 0

    if args.command == "ast":
        if args.format == "text":
            text = ast_text(result.program)
        elif args.format == "json":
            text = json_text(_envelope("ast", ast=ast.node_to_dict(result.program)))
        else:
            text = ast_dot(result.program)
        _write(text, args.output)
        return 0

    if args.command == "compare":
        data = comparison_summary(result.parse_tree, result.program)
        if args.json:
            print(json_text(_envelope("compare", **data)))
        else:
            print(f"Parse tree nodes: {data['parse_tree_nodes']}")
            print(f"AST nodes: {data['ast_nodes']}")
            print(f"Concrete nodes removed: {data['removed_concrete_nodes']}")
            print(data["explanation"])
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return execute(args)
    except SiplSyntaxError as exc:
        payload = _envelope(
            "error",
            error={"type": "syntax", "message": exc.message, "line": exc.line, "column": exc.column},
        )
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"Syntax error: {exc}", file=sys.stderr)
        return 2
    except (SiplRuntimeError, ValueError) as exc:
        payload = _envelope("error", error={"type": "runtime", "message": str(exc)})
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"Runtime error: {exc}", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"I/O error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

