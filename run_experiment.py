"""
run_experiment.py
=================
Reproduces the 20-simulation benchmark experiment described in the paper.

Each simulation uses a batch of 1,000 equations of a fixed length L,
starting at L=5 tokens and increasing by 20 tokens per simulation
(so L = 5, 25, 45, ..., 385), matching the paper's Table 11 / Table 12 design.

Both the STD and DBZ calculators are run on the same equation set.
Results are printed as a CSV table and optionally saved.

Usage
-----
  python run_experiment.py
  python run_experiment.py --equations-per-sim 1000 --output results.csv
  python run_experiment.py --seed 42

Reference:
  P. Jean-Paul and S. Wahid, "A Proof-of-Concept Division-by-Zero
  Calculator Using Semi-structured Complex Numbers," 2024.
"""

import argparse
import csv
import os
import sys
import time
import tracemalloc

from equation_generator import generate_equations
from calculator_std import run_std_calculator, benchmark_std
from calculator_dbz import run_dbz_calculator, benchmark_dbz


# ---------------------------------------------------------------------------
# Simulation parameters — matching the paper
# ---------------------------------------------------------------------------

N_SIMULATIONS      = 20       # Paper ran 20 simulations
EQ_PER_SIM         = 1_000    # 1,000 equations per simulation
MIN_VAL            = -1       # Operand range: integers in [-1, 1]
MAX_VAL            = 1        # (maximises DBZ probability)
BASE_LENGTH        = 5        # First simulation: L = 5
LENGTH_INCREMENT   = 20       # Each subsequent simulation adds 20 tokens
SEED               = 42       # Fixed seed for reproducibility


def count_dbz_in_equations(equations):
    """Count how many equations contain at least one division operator
    whose right operand evaluates to (0,0,0)."""
    # Approximate: count '/' tokens — exact count requires evaluation
    return sum(1 for eq in equations if '/' in eq)


def count_dbz_operations(equations):
    """Count total '/' operator tokens across all equations."""
    return sum(eq.split().count('/') for eq in equations)


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def run_experiment(n_sims, eq_per_sim, seed, output_csv=None):
    print(f"{'='*72}")
    print(f"  Semi-structured Complex Number Calculator Benchmark")
    print(f"  Simulations: {n_sims}  |  Equations/sim: {eq_per_sim}  |  Seed: {seed}")
    print(f"{'='*72}\n")

    header_std = [
        'Simulation', 'Length_L', 'Ops_per_eq',
        'N_eq_with_DBZ', 'Total_DBZ_ops',
        'STD_peak_memory_bytes', 'STD_avg_mem_per_op',
        'STD_output_bytes', 'STD_time_s',
        'STD_ops_per_s', 'STD_eq_completed'
    ]
    header_dbz = [
        'DBZ_peak_memory_bytes', 'DBZ_avg_mem_per_op',
        'DBZ_output_bytes', 'DBZ_time_s',
        'DBZ_ops_per_s', 'DBZ_eq_completed'
    ]

    rows = []

    for sim in range(1, n_sims + 1):
        L = BASE_LENGTH + (sim - 1) * LENGTH_INCREMENT   # token length
        ops_per_eq = (L - 1) // 2                        # number of operators

        # Generate equations for this simulation
        equations = generate_equations(
            n=eq_per_sim,
            min_val=MIN_VAL,
            max_val=MAX_VAL,
            min_length=L,
            max_length=L,
            seed=seed + sim   # unique seed per simulation
        )

        n_eq_dbz  = count_dbz_in_equations(equations)
        n_dbz_ops = count_dbz_operations(equations)

        # --- Run STD ---
        std_data = benchmark_std(equations)
        std_out_str = '\n'.join(std_data['results']) + '\n'
        std_out_bytes = len(std_out_str.encode())
        std_total_ops = std_data['equations_completed'] * ops_per_eq
        std_avg_mem = (std_data['peak_memory_bytes'] / std_total_ops
                       if std_total_ops > 0 else 0)
        std_ops_per_s = (std_data['equations_completed'] * ops_per_eq /
                         std_data['processing_time_s']
                         if std_data['processing_time_s'] > 0 else 0)

        # --- Run DBZ ---
        dbz_data = benchmark_dbz(equations)
        dbz_out_str = '\n'.join(dbz_data['results']) + '\n'
        dbz_out_bytes = len(dbz_out_str.encode())
        dbz_total_ops = dbz_data['equations_completed'] * ops_per_eq
        dbz_avg_mem = (dbz_data['peak_memory_bytes'] / dbz_total_ops
                       if dbz_total_ops > 0 else 0)
        dbz_ops_per_s = (dbz_data['equations_completed'] * ops_per_eq /
                         dbz_data['processing_time_s']
                         if dbz_data['processing_time_s'] > 0 else 0)

        row = {
            'Simulation':            sim,
            'Length_L':              L,
            'Ops_per_eq':            ops_per_eq,
            'N_eq_with_DBZ':         n_eq_dbz,
            'Total_DBZ_ops':         n_dbz_ops,
            # STD
            'STD_peak_memory_bytes': std_data['peak_memory_bytes'],
            'STD_avg_mem_per_op':    round(std_avg_mem, 4),
            'STD_output_bytes':      std_out_bytes,
            'STD_time_s':            round(std_data['processing_time_s'], 6),
            'STD_ops_per_s':         round(std_ops_per_s, 0),
            'STD_eq_completed':      std_data['equations_completed'],
            # DBZ
            'DBZ_peak_memory_bytes': dbz_data['peak_memory_bytes'],
            'DBZ_avg_mem_per_op':    round(dbz_avg_mem, 4),
            'DBZ_output_bytes':      dbz_out_bytes,
            'DBZ_time_s':            round(dbz_data['processing_time_s'], 6),
            'DBZ_ops_per_s':         round(dbz_ops_per_s, 0),
            'DBZ_eq_completed':      dbz_data['equations_completed'],
        }
        rows.append(row)

        # Console progress
        print(f"Sim {sim:2d}  L={L:4d}  "
              f"STD: {std_data['equations_completed']:4d}/{eq_per_sim} done "
              f"({std_data['processing_time_s']:.4f}s)  |  "
              f"DBZ: {dbz_data['equations_completed']:4d}/{eq_per_sim} done "
              f"({dbz_data['processing_time_s']:.4f}s)")

    print()

    # Print summary table
    print(f"{'Sim':>3} {'L':>5} {'STD_done':>8} {'STD_t(s)':>10} "
          f"{'STD_mem(B)':>12} {'DBZ_done':>8} {'DBZ_t(s)':>10} {'DBZ_mem(B)':>12}")
    print('-' * 75)
    for r in rows:
        print(f"{r['Simulation']:3d} {r['Length_L']:5d} "
              f"{r['STD_eq_completed']:8d} {r['STD_time_s']:10.4f} "
              f"{r['STD_peak_memory_bytes']:12d} "
              f"{r['DBZ_eq_completed']:8d} {r['DBZ_time_s']:10.4f} "
              f"{r['DBZ_peak_memory_bytes']:12d}")

    # Optionally write CSV
    if output_csv:
        all_keys = list(rows[0].keys())
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResults written to: {output_csv}")

    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run the 20-simulation benchmark from the paper."
    )
    parser.add_argument('--sims',           type=int, default=N_SIMULATIONS,
                        help=f'Number of simulations (default: {N_SIMULATIONS})')
    parser.add_argument('--eq-per-sim',     type=int, default=EQ_PER_SIM,
                        help=f'Equations per simulation (default: {EQ_PER_SIM})')
    parser.add_argument('--seed',           type=int, default=SEED,
                        help=f'Base RNG seed (default: {SEED})')
    parser.add_argument('--output', '-o',   type=str, default='results.csv',
                        help='Output CSV file (default: results.csv)')
    args = parser.parse_args()

    run_experiment(
        n_sims=args.sims,
        eq_per_sim=args.eq_per_sim,
        seed=args.seed,
        output_csv=args.output,
    )
