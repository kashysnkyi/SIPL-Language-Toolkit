"""Construction of course-style semantic terms from SIPL AST."""

from __future__ import annotations

from . import ast


_arithmetic = {"+": "add", "-": "sub", "*": "mul", "div": "div", "mod": "mod"}
_comparison = {"=": "eq", "!=": "neq", "<": "lt", "<=": "le", ">": "gr", ">=": "ge"}


def expression_term(expression: ast.Expr) -> str:
    if isinstance(expression, ast.Number):
        return str(expression.value)
    if isinstance(expression, ast.Variable):
        return f"{expression.name}^⇒"
    if isinstance(expression, ast.BoolLiteral):
        return "true" if expression.value else "false"
    if isinstance(expression, ast.UnaryExpr):
        operator = "neg" if expression.operator == "-" else "not"
        return f"S^1({operator}, {expression_term(expression.operand)})"
    if isinstance(expression, ast.BinaryExpr):
        return (
            f"S^2({_arithmetic[expression.operator]}, "
            f"{expression_term(expression.left)}, {expression_term(expression.right)})"
        )
    if isinstance(expression, ast.Comparison):
        return (
            f"S^2({_comparison[expression.operator]}, "
            f"{expression_term(expression.left)}, {expression_term(expression.right)})"
        )
    if isinstance(expression, ast.BoolBinary):
        return (
            f"S^2({expression.operator}, "
            f"{expression_term(expression.left)}, {expression_term(expression.right)})"
        )
    raise TypeError(f"Unsupported expression {type(expression).__name__}")


def statement_term(statement: ast.Statement) -> str:
    if isinstance(statement, ast.Assignment):
        return f"AS^{statement.name}({expression_term(statement.expression)})"
    if isinstance(statement, ast.Skip):
        return "id"
    if isinstance(statement, ast.Block):
        terms = [statement_term(child) for child in statement.statements]
        return " · ".join(terms) if terms else "id"
    if isinstance(statement, ast.If):
        return (
            f"IF({expression_term(statement.condition)}, "
            f"{statement_term(statement.then_branch)}, {statement_term(statement.else_branch)})"
        )
    if isinstance(statement, ast.While):
        return f"WH({expression_term(statement.condition)}, {statement_term(statement.body)})"
    raise TypeError(f"Unsupported statement {type(statement).__name__}")


def semantic_term(program: ast.Program) -> str:
    return statement_term(program.body)

