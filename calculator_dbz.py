"""
calculator_dbz.py
=================
Division-by-Zero (DBZ) arithmetic calculator for semi-structured
complex numbers.

Uses the totalized algebra H: when a division-by-zero operation is
encountered, the divisor is replaced by the unstructured unit p = (0,0,1)
and computation continues without raising an exception.  The result
propagates algebraically through all subsequent operations.

Implements the General Calculator Algorithm (Table 9) with
Arithmetic Machine DBZ (Table 8) of the paper.

Reference:
  P. Jean-Paul and S. Wahid, "A Proof-of-Concept Division-by-Zero
  Calculator Using Semi-structured Complex Numbers," 2024.

Usage
-----
  python calculator_dbz.py equations.txt
  python calculator_dbz.py equations.txt --output results_dbz.txt
"""

import sys
import time
import tracemalloc
import argparse

from arithmetic import (
    infix_to_postfix,
    evaluate_postfix,
    arithmetic_machine_dbz,
    _fmt,
)


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

def run_dbz_calculator(equations):
    """
    Process a list of infix equation strings with the DBZ calculator.

    Every equation is completed — division by zero is handled algebraically
    by substituting p = (0,0,1) for the zero divisor, so no equation aborts.

    Parameters
    ----------
    equations : list of str

    Returns
    -------
    dict with keys:
      results            : list of str  — one result string per equation
      equations_completed: int          — always equals len(equations)
      dbz_count          : int          — number of DBZ substitutions made
                                         (counted at machine level — see note)
    """
    results = []
    equations_completed = 0

    for eq in equations:
        try:
            postfix = infix_to_postfix(eq)
            triple  = evaluate_postfix(postfix, arithmetic_machine_dbz)
            results.append(_fmt(triple))
            equations_completed += 1
        except Exception as e:
            # Should not occur under normal operation; kept for robustness
            results.append(f"ERR:{e}")

    return {
        'results':             results,
        'equations_completed': equations_completed,
    }


# ---------------------------------------------------------------------------
# Benchmark wrapper  (matches the paper's measurement approach)
# ---------------------------------------------------------------------------

def benchmark_dbz(equations):
    """
    Run the DBZ calculator and collect timing and memory measurements.

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

    data = run_dbz_calculator(equations)

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
        description="DBZ calculator — processes equations with totalized arithmetic."
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
    data = benchmark_dbz(equations)

    # Write results
    output_text = '\n'.join(data['results']) + '\n'
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
    else:
        sys.stdout.write(output_text)

    # Summary
    if args.summary or args.output:
        n_total   = len(equations)
        n_done    = data['equations_completed']
        t_s       = data['processing_time_s']
        mem_bytes = data['peak_memory_bytes']
        ops_per_s = n_done / t_s if t_s > 0 else float('inf')

        print(f"\n--- DBZ Calculator Summary ---", file=sys.stderr)
        print(f"  Equations submitted   : {n_total}", file=sys.stderr)
        print(f"  Equations completed   : {n_done}", file=sys.stderr)
        print(f"  Processing time (s)   : {t_s:.6f}", file=sys.stderr)
        print(f"  Peak memory (bytes)   : {mem_bytes}", file=sys.stderr)
        print(f"  Operations/sec        : {ops_per_s:.0f}", file=sys.stderr)
        if args.output:
            output_size = len(output_text.encode())
            print(f"  Output size (bytes)   : {output_size}", file=sys.stderr)


if __name__ == '__main__':
    main()
