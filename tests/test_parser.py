from sipl import ast
from sipl.parser import SiplParser


def test_typed_ast_and_source_span():
    source = "begin\n  X := 1 + 2\nend"
    program = SiplParser().parse(source).program
    assignment = program.body.statements[0]
    assert isinstance(assignment, ast.Assignment)
    assert isinstance(assignment.expression, ast.BinaryExpr)
    assert assignment.name == "X"
    assert assignment.span.line == 2
    assert assignment.span.column == 3
    assert source[assignment.span.start_pos : assignment.span.end_pos] == "X := 1 + 2"


def test_precedence_and_boolean_ast():
    program = SiplParser().parse(
        "begin if X + 2 * 3 >= 7 and true then skip else X := -1 end"
    ).program
    statement = program.body.statements[0]
    assert isinstance(statement, ast.If)
    assert isinstance(statement.condition, ast.BoolBinary)
    assert statement.condition.operator == "and"
    comparison = statement.condition.left
    assert isinstance(comparison, ast.Comparison)
    assert isinstance(comparison.left, ast.BinaryExpr)
    assert comparison.left.operator == "+"
    assert isinstance(comparison.left.right, ast.BinaryExpr)
    assert comparison.left.right.operator == "*"


def test_ast_json_is_stable():
    program = SiplParser().parse("begin skip end").program
    data = ast.node_to_dict(program)
    assert data["kind"] == "Program"
    assert data["body"]["kind"] == "Block"
    assert data["body"]["statements"][0]["kind"] == "Skip"

