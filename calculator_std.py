"""
calculator_std.py
=================
Standard (STD) arithmetic calculator for semi-structured complex numbers.

Uses exception handling to deal with division by zero: when a DBZ
operation is encountered the equation is aborted, an error message is
recorded, and the calculator resets for the next equation.

Implements the General Calculator Algorithm (Table 9) with
Arithmetic Machine STD (Table 7) of the paper.

Reference:
  P. Jean-Paul and S. Wahid, "A Proof-of-Concept Division-by-Zero
  Calculator Using Semi-structured Complex Numbers," 2024.

Usage
-----
  python calculator_std.py equations.txt
  python calculator_std.py equations.txt --output results_std.txt
"""

import sys
import time
import tracemalloc
import argparse

from arithmetic import (
    infix_to_postfix,
    evaluate_postfix,
    arithmetic_machine_std,
    _fmt,
)


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

def run_std_calculator(equations):
    """
    Process a list of infix equation strings with the STD calculator.

    For each equation:
      1. Convert infix → postfix  (Algorithm 14)
      2. Evaluate postfix using Arithmetic Machine STD  (Algorithm 15 / Table 7)
      3. On ZeroDivisionError: record "ERR" and move to next equation.

    Parameters
    ----------
    equations : list of str

    Returns
    -------
    dict with keys:
      results            : list of str  — one result string per equation
      equations_completed: int
      dbz_count          : int  — number of equations that triggered DBZ
    """
    results = []
    equations_completed = 0
    dbz_count = 0

    for eq in equations:
        try:
            postfix = infix_to_postfix(eq)
            triple  = evaluate_postfix(postfix, arithmetic_machine_std)
            results.append(_fmt(triple))
            equations_completed += 1
        except ZeroDivisionError:
            results.append("ERR")
            dbz_count += 1
        except Exception as e:
            results.append(f"ERR:{e}")

    return {
        'results':             results,
        'equations_completed': equations_completed,
        'dbz_count':           dbz_count,
    }


# ---------------------------------------------------------------------------
# Benchmark wrapper  (matches the paper's measurement approach)
# ---------------------------------------------------------------------------

def benchmark_std(equations):
    """
    Run the STD calculator and collect timing and memory measurements.

    Timing  : time.perf_counter() — wall-clock seconds
    Memory  : tracemalloc peak    — bytes

    Returns
    -------
    dict with all results plus:
      processing_time_s  : float  — elapsed wall-clock seconds
      peak_memory_bytes  : int    — peak memory in bytes
    """
    tracemalloc.start()
    t_start = time.perf_counter()

    data = run_std_calculator(equations)

    t_end = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    data['processing_time_s'] = t_end - t_start
    data['peak_memory_bytes'] = peak
    return data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="STD calculator — processes equations with exception handling."
    )
    parser.add_argument('equations_file',
                        help='Path to equations file (one equation per line)')
    parser.add_argument('--output', '-o', default=None,
                        help='Write results to this file (default: stdout)')
    parser.add_argument('--summary', action='store_true',
                        help='Print benchmark summary to stderr')
    args = parser.parse_args()

    # Load equations
    with open(args.equations_file, 'r') as f:
        equations = [line.strip() for line in f if line.strip()]

    # Run
    data = benchmark_std(equations)

    # Write results
    output_text = '\n'.join(data['results']) + '\n'
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
    else:
        sys.stdout.write(output_text)

    # Summary
    if args.summary or args.output:
        n_total    = len(equations)
        n_done     = data['equations_completed']
        n_dbz      = data['dbz_count']
        t_s        = data['processing_time_s']
        mem_bytes  = data['peak_memory_bytes']
        ops_per_s  = n_done / t_s if t_s > 0 else float('inf')

        print(f"\n--- STD Calculator Summary ---", file=sys.stderr)
        print(f"  Equations submitted   : {n_total}", file=sys.stderr)
        print(f"  Equations completed   : {n_done}", file=sys.stderr)
        print(f"  DBZ aborts (ERR)      : {n_dbz}", file=sys.stderr)
        print(f"  Processing time (s)   : {t_s:.6f}", file=sys.stderr)
        print(f"  Peak memory (bytes)   : {mem_bytes}", file=sys.stderr)
        print(f"  Operations/sec        : {ops_per_s:.0f}", file=sys.stderr)
        if args.output:
            output_size = len(output_text.encode())
            print(f"  Output size (bytes)   : {output_size}", file=sys.stderr)


if __name__ == '__main__':
    main()
