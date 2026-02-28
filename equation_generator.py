"""
equation_generator.py
=====================
Generates random valid infix arithmetic equations of semi-structured
complex numbers in triple format.

Implements Algorithm 5 of the paper exactly.

Reference:
  P. Jean-Paul and S. Wahid, "A Proof-of-Concept Division-by-Zero
  Calculator Using Semi-structured Complex Numbers," 2024.
"""

import random


OPERATORS = ['+', '-', '*', '/']


def generate_equation(min_val, max_val, length, rng=None):
    """
    Generate one random infix equation of semi-structured complex number
    triples.

    Implements Algorithm 5 of the paper.

    Rules (from the paper):
      i.   Length L must be odd and >= 3.
      ii.  Equation starts and ends with an operand.
      iii. Operators occupy even positions (1-indexed); operands odd.
      iv.  No brackets — operator precedence governs evaluation order.

    Parameters
    ----------
    min_val : int   Minimum integer value for each component of a triple.
    max_val : int   Maximum integer value for each component of a triple.
    length  : int   Number of tokens (operands + operators).  Forced odd >= 3.
    rng     : random.Random, optional  — supply a seeded RNG for reproducibility.

    Returns
    -------
    str  — space-separated infix equation, e.g. "1,0,-1 + 0,0,0 / 1,1,0"
    """
    if rng is None:
        rng = random

    # Step 2 — enforce minimum length
    if length < 3:
        length = 3

    # Step 3 — enforce odd length
    if length % 2 == 0:
        length += 1

    # Step 4 — create equation accumulator
    tokens = []

    # Steps 6-12 — build token list
    for t in range(1, length + 1):          # T = 1 to Equation Length
        if t % 2 == 0:                      # Step 7 — even position → operator
            tokens.append(rng.choice(OPERATORS))
        else:                               # Step 8 — odd position → operand
            x = rng.randint(min_val, max_val)   # Step 9
            y = rng.randint(min_val, max_val)   # Step 10
            z = rng.randint(min_val, max_val)   # Step 11
            tokens.append(f"{x},{y},{z}")       # Step 12

    # Step 13 — return equation string
    return ' '.join(tokens)


def generate_equations(n, min_val, max_val, min_length, max_length, seed=42):
    """
    Generate n equations with random lengths in [min_length, max_length].

    Lengths are drawn uniformly at random from odd values in the range.
    The RNG is seeded for reproducibility.

    Parameters
    ----------
    n          : int   Number of equations to generate.
    min_val    : int   Minimum operand component value.
    max_val    : int   Maximum operand component value.
    min_length : int   Minimum equation token length (forced odd).
    max_length : int   Maximum equation token length (forced odd).
    seed       : int   RNG seed for reproducibility.

    Returns
    -------
    list of str  — list of infix equation strings.
    """
    rng = random.Random(seed)

    # Build pool of valid (odd) lengths
    odd_lengths = [l for l in range(min_length, max_length + 1) if l % 2 == 1]
    if not odd_lengths:
        odd_lengths = [3]

    equations = []
    for _ in range(n):
        L = rng.choice(odd_lengths)
        eq = generate_equation(min_val, max_val, L, rng=rng)
        equations.append(eq)

    return equations


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import argparse, sys

    parser = argparse.ArgumentParser(
        description="Generate random semi-structured complex number equations."
    )
    parser.add_argument('-n',          type=int, default=20000, help='Number of equations (default: 20000)')
    parser.add_argument('--min-val',   type=int, default=-1,    help='Min operand component value (default: -1)')
    parser.add_argument('--max-val',   type=int, default=1,     help='Max operand component value (default: 1)')
    parser.add_argument('--min-len',   type=int, default=3,     help='Min equation length in tokens (default: 3)')
    parser.add_argument('--max-len',   type=int, default=203,   help='Max equation length in tokens (default: 203)')
    parser.add_argument('--seed',      type=int, default=42,    help='RNG seed (default: 42)')
    parser.add_argument('-o',          type=str, default=None,  help='Output file (default: stdout)')
    args = parser.parse_args()

    equations = generate_equations(
        n=args.n,
        min_val=args.min_val,
        max_val=args.max_val,
        min_length=args.min_len,
        max_length=args.max_len,
        seed=args.seed
    )

    if args.o:
        with open(args.o, 'w') as f:
            for eq in equations:
                f.write(eq + '\n')
        print(f"Wrote {len(equations)} equations to {args.o}", file=sys.stderr)
    else:
        for eq in equations:
            print(eq)
