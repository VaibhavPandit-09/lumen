"""
Safe, sandboxed mathematical expression and percentage evaluator.
"""

from __future__ import annotations

import ast
import math
import operator
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CalculatorResult:
    expression: str
    result_str: str
    numeric_value: float


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS: Dict[str, Any] = {
    "sqrt": math.sqrt,
    "cbrt": math.cbrt if hasattr(math, "cbrt") else lambda x: x ** (1 / 3),
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "hypot": math.hypot,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": lambda a: math.factorial(int(a)),
    "gcd": lambda a, b: math.gcd(int(a), int(b)),
    "lcm": lambda a, b: abs(int(a) * int(b)) // math.gcd(int(a), int(b)) if math.gcd(int(a), int(b)) != 0 else 0,
    "comb": lambda n, k: math.comb(int(n), int(k)) if hasattr(math, "comb") else 0,
    "perm": lambda n, k=None: (math.perm(int(n), int(k)) if k is not None else math.perm(int(n))) if hasattr(math, "perm") else 0,
    "deg": math.degrees,
    "degrees": math.degrees,
    "rad": math.radians,
    "radians": math.radians,
}
# Filter out None entries for Python version compatibility
SAFE_FUNCTIONS = {k: v for k, v in SAFE_FUNCTIONS.items() if v is not None}

SAFE_CONSTANTS: Dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluates an AST node in a safe sandbox."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Invalid constant type")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)

        # Avoid astronomical exponents that hang CPU
        if op_type is ast.Pow:
            if abs(right) > 1000 or abs(left) > 1e10:
                raise ValueError("Exponent too large")

        return float(SAFE_OPERATORS[op_type](left, right))

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type}")
        operand = _eval_node(node.operand)
        return float(SAFE_OPERATORS[op_type](operand))

    if isinstance(node, ast.Name):
        name_lower = node.id.lower()
        if name_lower in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[name_lower]
        raise ValueError(f"Unknown variable: {node.id}")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Invalid function call")
        func_name = node.func.id.lower()
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Unknown function: {func_name}")
        args = [_eval_node(arg) for arg in node.args]
        return float(SAFE_FUNCTIONS[func_name](*args))

    raise ValueError(f"Unsupported AST node: {type(node)}")


def preprocess_expression(expr: str) -> str:
    """Normalizes human expressions (e.g. '15% of 400', '400 + 15%', 'sin(45 deg)', '^' as power)."""
    s = expr.strip()

    # Normalize power operator '^' to '**'
    s = s.replace("^", "**")

    # Replace 'X deg' / 'X degrees' with 'radians(X)'
    s = re.sub(r"([\d\.]+)\s*(?:deg|degrees)\b", r"radians(\1)", s, flags=re.IGNORECASE)
    # Replace 'X rad' / 'X radians' with '\1'
    s = re.sub(r"([\d\.]+)\s*(?:rad|radians)\b", r"(\1)", s, flags=re.IGNORECASE)

    # Replace 'X% of Y' with '(X / 100) * Y'
    s = re.sub(
        r"([\d\.]+)\s*%\s*(?:of|\*)\s*([\d\.]+)",
        r"((\1 / 100.0) * \2)",
        s,
        flags=re.IGNORECASE,
    )

    # Replace 'X + Y%' with 'X * (1 + Y / 100)'
    s = re.sub(
        r"([\d\.]+)\s*\+\s*([\d\.]+)\s*%",
        r"(\1 * (1.0 + (\2 / 100.0)))",
        s,
    )

    # Replace 'X - Y%' with 'X * (1 - Y / 100)'
    s = re.sub(
        r"([\d\.]+)\s*\-\s*([\d\.]+)\s*%",
        r"(\1 * (1.0 - (\2 / 100.0)))",
        s,
    )

    # Replace lone 'X%' with '(X / 100.0)'
    s = re.sub(r"([\d\.]+)\s*%", r"(\1 / 100.0)", s)

    return s


def evaluate_expression(query: str) -> Optional[CalculatorResult]:
    """
    Attempts to safely evaluate query as a mathematical expression.
    Returns CalculatorResult if valid, None otherwise.
    """
    if not query or len(query.strip()) < 2:
        return None

    raw_query = query.strip()

    # Fast rejection if query contains no numbers or math symbols
    has_math_tokens = any(ch in raw_query for ch in "0123456789+-*/%^=()")
    has_func_tokens = any(
        fn in raw_query.lower()
        for fn in [
            "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "log", "pi",
            "tau", "abs", "gcd", "lcm", "hypot", "exp", "deg", "rad", "cbrt",
            "round", "ceil", "floor", "factorial", "comb", "perm",
        ]
    )

    if not (has_math_tokens or has_func_tokens):
        return None

    # Remove trailing '=' if user typed e.g. "2 + 2 ="
    cleaned = raw_query.rstrip("=").strip()

    try:
        normalized = preprocess_expression(cleaned)
        tree = ast.parse(normalized, mode="eval")
        val = _eval_node(tree.body)

        if math.isnan(val) or math.isinf(val):
            return None

        # Format result nicely
        if val.is_integer() and abs(val) < 1e15:
            res_str = str(int(val))
        else:
            # Round float precision
            res_str = f"{val:.10g}"

        return CalculatorResult(
            expression=raw_query,
            result_str=res_str,
            numeric_value=val,
        )
    except Exception:
        return None
