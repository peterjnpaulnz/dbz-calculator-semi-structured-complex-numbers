"""
arithmetic.py
=============
Arithmetic operations for semi-structured complex numbers.

A semi-structured complex number has the form:
    h = x + yi + zp
and is represented as the ordered triple (x, y, z).

This module implements:
  - Addition
  - Subtraction
  - Multiplication  (Table 16 from the paper)
  - Division        (Arithmetic Machine STD — Table 7)
  - Division        (Arithmetic Machine DBZ — Table 8)
  - The shared postfix converter (Algorithm 14)
  - The shared postfix evaluator (Algorithm 15)

Reference:
  P. Jean-Paul and S. Wahid, "A Proof-of-Concept Division-by-Zero
  Calculator Using Semi-structured Complex Numbers," 2024.
"""

import math


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(triple):
    """Format a triple (x, y, z) as a compact string for output."""
    x, y, z = triple
    def _f(v):
        # Show as int if value is a whole number, else as float
        return str(int(v)) if isinstance(v, float) and v.is_integer() else str(round(v, 6))
    return f"{_f(x)},{_f(y)},{_f(z)}"


# ---------------------------------------------------------------------------
# Core arithmetic on triples
# ---------------------------------------------------------------------------

def add(xyz, abc):
    """Add two semi-structured complex numbers.  (x+a, y+b, z+c)"""
    x, y, z = xyz
    a, b, c = abc
    return (x + a, y + b, z + c)


def subtract(xyz, abc):
    """Subtract abc from xyz.  (x-a, y-b, z-c)"""
    x, y, z = xyz
    a, b, c = abc
    return (x - a, y - b, z - c)


def multiply(xyz, abc):
    """
    Multiply two semi-structured complex numbers.
    Implements Table 16 of the paper exactly.

    Step 2:  A = xa - yb - zc*  (* paper uses 'zp' which encodes as z*c
             B = xb + ya
    Step 3:  C = xc + za
             D = yc + zb
    Steps 4-6:  F = atan2(B, A)  (with special cases)
    Steps 8-10: G = atan2(D, C)  (with special cases)
    Step 12: new_X = sqrt(A²+B²) * cos(F - G)
    Step 13: new_Y = sqrt(A²+B²) * sin(F - G)
    Step 14: new_Z = sqrt(C²+D²)
    """
    x, y, z = xyz
    a, b, c = abc

    # Step 2
    A = x * a - y * b - z * c   # Note: paper writes "za·p² = -za" absorbed into A
    B = x * b + y * a

    # Step 3
    C = x * c + z * a
    D = y * c + z * b

    # Steps 4-6: compute F
    if A == 0 and B == 0:
        F = math.pi
    elif A == 0 and B != 0:
        F = math.pi / 2
    else:
        F = math.atan2(B, A)   # atan⁻¹(B/A) using atan2 for correct quadrant

    # Steps 8-10: compute G
    if C == 0 and D == 0:
        G = math.pi
    elif C == 0 and D != 0:
        G = math.pi / 2
    else:
        G = math.atan2(D, C)

    # Steps 12-14
    new_X = math.sqrt(A ** 2 + B ** 2) * math.cos(F - G)
    new_Y = math.sqrt(A ** 2 + B ** 2) * math.sin(F - G)
    new_Z = math.sqrt(C ** 2 + D ** 2)

    return (new_X, new_Y, new_Z)


# ---------------------------------------------------------------------------
# Arithmetic Machines
# ---------------------------------------------------------------------------

def arithmetic_machine_std(xyz, abc, op):
    """
    Arithmetic Machine STD — Table 7 of the paper.

    Performs one arithmetic operation on two semi-structured complex numbers.
    On division by zero (a, b, c) == (0, 0, 0), raises ZeroDivisionError.

    Parameters
    ----------
    xyz : tuple  First operand (x, y, z)
    abc : tuple  Second operand (a, b, c)
    op  : str    One of '+', '-', '/', '*'

    Returns
    -------
    tuple : result triple (new_X, new_Y, new_Z)

    Raises
    ------
    ZeroDivisionError : when dividing by (0, 0, 0)
    """
    if op == '+':
        return add(xyz, abc)

    if op == '-':
        return subtract(xyz, abc)

    if op == '*':
        return multiply(xyz, abc)

    if op == '/':
        a, b, c = abc
        # Step 7 — Try: if abc == (0,0,0) raise exception (Catch → error)
        if a == 0 and b == 0 and c == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        # Step 9 — R = 1 / (a²+b²+c²)
        R = 1.0 / (a * a + b * b + c * c)
        # Step 10 — inverse of abc
        new_a = R * a
        new_b = -R * b
        new_c = -R * c
        # Step 11 — multiply xyz by the inverse
        return multiply(xyz, (new_a, new_b, new_c))

    raise ValueError(f"Unknown operator: {op!r}")


def arithmetic_machine_dbz(xyz, abc, op):
    """
    Arithmetic Machine DBZ — Table 8 of the paper.

    Identical to STD except that on division by zero, the divisor is
    replaced by the unstructured unit p = (0, 0, 1) instead of raising
    an exception.  This yields a totalized result that propagates through
    subsequent operations.

    Parameters
    ----------
    xyz : tuple  First operand (x, y, z)
    abc : tuple  Second operand (a, b, c)
    op  : str    One of '+', '-', '/', '*'

    Returns
    -------
    tuple : result triple (new_X, new_Y, new_Z)
    """
    if op == '+':
        return add(xyz, abc)

    if op == '-':
        return subtract(xyz, abc)

    if op == '*':
        return multiply(xyz, abc)

    if op == '/':
        a, b, c = abc
        # Step 7 — If abc == (0,0,0) then set abc = (0,0,1)  [p = 1/0]
        if a == 0 and b == 0 and c == 0:
            a, b, c = 0, 0, 1
        # Compute R = 1/(a²+b²+c²), then multiply
        R = 1.0 / (a * a + b * b + c * c)
        new_a = R * a
        new_b = -R * b
        new_c = -R * c
        return multiply(xyz, (new_a, new_b, new_c))

    raise ValueError(f"Unknown operator: {op!r}")


# ---------------------------------------------------------------------------
# Postfix converter  (Algorithm 14 — shared by both calculators)
# ---------------------------------------------------------------------------

OPERATORS   = set(['+', '-', '*', '/'])
PRECEDENCE  = {'+': 1, '-': 1, '*': 2, '/': 2}


def infix_to_postfix(equation_string):
    """
    Convert an infix equation string of semi-structured complex numbers
    to postfix (Reverse Polish) notation.

    Implements Algorithm 14 of the paper.

    Tokens are separated by spaces.  Operands are triples of the form
    "x,y,z".  Operators are +, -, *, /.

    Parameters
    ----------
    equation_string : str

    Returns
    -------
    list of str  — postfix token sequence
    """
    tokens = equation_string.strip().split()
    operator_stack = []
    output = []

    for token in tokens:                                    # Step 4
        if token not in OPERATORS:                          # Step 5 — operand
            output.append(token)
        else:                                               # Step 8 — operator
            # Remove operators of higher or equal precedence first
            while (operator_stack and
                   operator_stack[-1] in OPERATORS and
                   PRECEDENCE[operator_stack[-1]] >= PRECEDENCE[token]):
                output.append(operator_stack.pop())
            operator_stack.append(token)

    # Step 9 — drain remaining operators
    while operator_stack:
        output.append(operator_stack.pop())

    return output


# ---------------------------------------------------------------------------
# Postfix evaluator  (Algorithm 15 — shared; uses chosen Arithmetic Machine)
# ---------------------------------------------------------------------------

def _parse_triple(token):
    """Parse 'x,y,z' token into a float triple."""
    parts = token.split(',')
    return (float(parts[0]), float(parts[1]), float(parts[2]))


def evaluate_postfix(postfix_tokens, machine_fn):
    """
    Evaluate a postfix token list using the supplied arithmetic machine.

    Implements Algorithm 15 of the paper.

    Parameters
    ----------
    postfix_tokens : list of str
    machine_fn     : callable  — arithmetic_machine_std or arithmetic_machine_dbz

    Returns
    -------
    tuple : result triple, or raises an exception (STD only)
    """
    operand_stack = []                                      # Step 2

    for token in postfix_tokens:                           # Step 4
        if token not in OPERATORS:                         # Step 5 — operand
            operand_stack.append(_parse_triple(token))
        else:                                              # Step 6 — operator
            second = operand_stack.pop()   # first pop = second operand
            first  = operand_stack.pop()   # second pop = first operand
            result = machine_fn(first, second, token)
            operand_stack.append(result)

    return operand_stack.pop()                             # Step 7
