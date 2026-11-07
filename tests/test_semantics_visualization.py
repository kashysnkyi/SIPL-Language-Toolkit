from sipl import ast
from sipl.parser import SiplParser
from sipl.semantics import semantic_term
from sipl.visualization import (
    ast_dot,
    ast_text,
    comparison_summary,
    parse_tree_dot,
    parse_tree_text,
    parse_tree_to_dict,
)


PARITY = """begin
while N > 1 do N := N - 2;
if N = 1 then R := 1 else R := 0
end"""


def test_semantic_term_matches_course_notation():
    program = SiplParser().parse(PARITY).program
    term = semantic_term(program)
    assert "WH(S^2(gr, N^⇒, 1), AS^N(S^2(sub, N^⇒, 2)))" in term
    assert "IF(S^2(eq, N^⇒, 1), AS^R(1), AS^R(0))" in term
    assert " · " in term


def test_parse_tree_renderers():
    result = SiplParser().parse("begin X := 1 end")
    data = parse_tree_to_dict(result.parse_tree)
    assert data["kind"] == "Rule"
    assert "start" in parse_tree_text(result.parse_tree)
    dot = parse_tree_dot(result.parse_tree)
    assert dot.startswith("digraph SIPL")
    assert "assignment" in dot


def test_ast_renderers_and_comparison():
    result = SiplParser().parse("begin X := 1 end")
    assert "Program" in ast_text(result.program)
    assert "Assignment" in ast_dot(result.program)
    summary = comparison_summary(result.parse_tree, result.program)
    assert summary["parse_tree_nodes"] > summary["ast_nodes"]
    assert summary["removed_concrete_nodes"] > 0
    assert ast.node_to_dict(result.program)["kind"] == "Program"

