import re  # For pattern matching to validate input

# ===============================
# FUNCTION: evaluate()
# ===============================
def evaluate(expr: str):
    """
    Safely evaluate a mathematical expression provided as a string.

    Supports:
        - Addition (+), Subtraction (-), Multiplication (*)
        - Division (/), Modulo (%)
        - Parentheses for grouping ()
        - Decimal numbers and spaces

    Args:
        expr (str): The math expression to evaluate, e.g., "2 + 3 * (4 - 1)"

    Returns:
        int/float/str: The evaluated result or an error message
    """
    try:
        # 1. Remove all spaces to simplify evaluation
        expr = expr.replace(" ", "")

        # 2. Validate expression: only allow numbers, operators, parentheses, and decimals
        # Regex breakdown:
        # [0-9] → digits
        # +\-*/% → math operators
        # .() → decimal point and parentheses
        # + → one or more characters
        if not re.fullmatch(r"[0-9+\-*/%.()]+", expr):
            return "Invalid characters in expression"

        # 3. Evaluate safely using eval()
        # - {"__builtins__": None} disables built-in functions for safety
        # - {} provides an empty global environment
        result = eval(expr, {"__builtins__": None}, {})

        # 4. If the result is a float but looks like an integer (e.g., 4.0), return it as int
        if isinstance(result, float) and result.is_integer():
            return int(result)

        return result

    # 5. Handle division by zero separately
    except ZeroDivisionError:
        return "Division by zero is not allowed"

    # 6. Catch any other errors (invalid syntax, etc.)
    except Exception:
        return "Invalid expression"
