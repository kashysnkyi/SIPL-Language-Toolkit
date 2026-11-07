"""Dependency-free local web application for SIPL Language Toolkit."""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from typing import Any

from . import ast
from .interpreter import Interpreter, SiplRuntimeError
from .parser import SiplParser, SiplSyntaxError
from .semantics import semantic_term
from .visualization import comparison_summary, parse_tree_to_dict


def parse_state(value: str | dict[str, Any] | None) -> dict[str, int]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {str(name): int(number) for name, number in value.items()}
    result: dict[str, int] = {}
    if not value.strip():
        return result
    for item in value.split(","):
        if "=" not in item:
            raise ValueError(f"State item must have NAME=INTEGER form: {item.strip()}")
        name, raw = (part.strip() for part in item.split("=", 1))
        if not name.isidentifier():
            raise ValueError(f"Invalid variable name: {name}")
        result[name] = int(raw)
    return result


def analyze_source(source: str) -> dict[str, Any]:
    result = SiplParser().parse(source)
    return {
        "ok": True,
        "ast": ast.node_to_dict(result.program),
        "parse_tree": parse_tree_to_dict(result.parse_tree),
        "semantic_term": semantic_term(result.program),
        "comparison": comparison_summary(result.parse_tree, result.program),
    }


def run_source(source: str, state: str | dict[str, Any] | None = None, step_limit: int = 10_000) -> dict[str, Any]:
    result = SiplParser().parse(source)
    execution = Interpreter(step_limit=step_limit).run(result.program, parse_state(state))
    return {
        "ok": True,
        "state": execution.state,
        "steps": execution.steps,
        "events": [event.to_dict() for event in execution.events],
        "semantic_term": semantic_term(result.program),
    }


def _error(exc: Exception) -> tuple[int, dict[str, Any]]:
    if isinstance(exc, SiplSyntaxError):
        return 400, {
            "ok": False,
            "error": {
                "type": "syntax",
                "message": exc.message,
                "line": exc.line,
                "column": exc.column,
                "context": exc.context,
            },
        }
    if isinstance(exc, (SiplRuntimeError, ValueError)):
        return 400, {"ok": False, "error": {"type": "runtime", "message": str(exc)}}
    return 500, {"ok": False, "error": {"type": "internal", "message": str(exc)}}


class SiplWebHandler(BaseHTTPRequestHandler):
    server_version = "SIPLToolkit/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict[str, Any]:
        size = int(self.headers.get("Content-Length", "0"))
        if size > 2_000_000:
            raise ValueError("Request is too large")
        return json.loads(self.rfile.read(size).decode("utf-8"))

    def do_GET(self) -> None:
        if self.path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        content = files("sipl.webui").joinpath("index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        try:
            payload = self._body()
            source = str(payload.get("source", ""))
            if self.path == "/api/analyze":
                self._json(200, analyze_source(source))
                return
            if self.path == "/api/run":
                self._json(
                    200,
                    run_source(
                        source,
                        payload.get("state", ""),
                        int(payload.get("step_limit", 10_000)),
                    ),
                )
                return
            self._json(404, {"ok": False, "error": {"type": "http", "message": "Not found"}})
        except Exception as exc:
            status, payload = _error(exc)
            self._json(status, payload)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local SIPL web interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), SiplWebHandler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"SIPL local site: {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

