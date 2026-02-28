# Division-by-Zero Calculator — Semi-structured Complex Numbers

Python implementation of two stack-based arithmetic calculators built over
the semi-structured complex number set **H**, as described in:

> P. Jean-Paul and S. Wahid, *"A Proof-of-Concept Division-by-Zero
> Calculator Using Semi-structured Complex Numbers,"* 2024.

---

## Overview

A **semi-structured complex number** has the form `h = x + yi + zp` and
is represented as the ordered triple `(x, y, z)`.  The unit `p = 1/0`
is the designated absorbing element that arises from division by zero.

Two calculators are implemented:

| Calculator | Division-by-zero handling |
|------------|--------------------------|
| **STD**    | Exception (`ZeroDivisionError`) — equation aborts |
| **DBZ**    | Totalized algebra — divisor replaced by `p = (0,0,1)`, computation continues |

Both share the same infix-to-postfix converter and postfix evaluator.
They differ only in their Arithmetic Machine.

---

## Requirements

- Python 3.8 or later
- No external dependencies — uses only the Python standard library
  (`math`, `random`, `time`, `tracemalloc`, `argparse`, `csv`)

---

## Files

| File | Description |
|------|-------------|
| `arithmetic.py` | Core arithmetic: add, subtract, multiply, divide, postfix converter/evaluator |
| `equation_generator.py` | Random infix equation generator (Algorithm 5 from the paper) |
| `calculator_std.py` | Standard calculator with exception handling |
| `calculator_dbz.py` | Division-by-zero calculator with totalized arithmetic |
| `run_experiment.py` | Reproduces the 20-simulation benchmark from the paper |
| `equations_20000.txt` | Pre-generated set of 20,000 test equations (seed=42) |

---

## Quick Start

### 1. Generate equations

```bash
# Use the pre-generated file, or generate fresh:
python equation_generator.py -n 20000 --min-val -1 --max-val 1 --seed 42 -o equations_20000.txt
```

### 2. Run the STD calculator

```bash
python calculator_std.py equations_20000.txt --output results_std.txt --summary
```

### 3. Run the DBZ calculator

```bash
python calculator_dbz.py equations_20000.txt --output results_dbz.txt --summary
```

### 4. Reproduce the paper's 20-simulation experiment

```bash
python run_experiment.py --seed 42 --output results.csv
```

This runs 20 simulations of 1,000 equations each, with equation length
increasing from 5 to 385 tokens in steps of 20.  Results are written to
`results.csv`.

---

## Algorithm reference

All algorithms are implemented exactly as specified in the paper:

| Algorithm | File | Function |
|-----------|------|----------|
| Table 5 — Equation generator | `equation_generator.py` | `generate_equation()` |
| Table 7 — Arithmetic Machine STD | `arithmetic.py` | `arithmetic_machine_std()` |
| Table 8 — Arithmetic Machine DBZ | `arithmetic.py` | `arithmetic_machine_dbz()` |
| Table 14 — Postfix converter | `arithmetic.py` | `infix_to_postfix()` |
| Table 15 — Postfix evaluator | `arithmetic.py` | `evaluate_postfix()` |
| Table 16 — Multiply function | `arithmetic.py` | `multiply()` |

---

## Equation format

Equations are space-separated infix expressions where:
- **Operands** are integer triples: `x,y,z`  (e.g. `1,-1,0`)
- **Operators** are: `+`, `-`, `*`, `/`
- No brackets — operator precedence governs evaluation order

Example equations:
```
1,0,0 + 0,1,0
-1,-1,1 * 0,0,0 / 1,1,0 + -1,0,1
1,0,0 / 0,0,0
```

The last equation produces `ERR` in the STD calculator and `0,0,1` (= p)
in the DBZ calculator.

---

## Reproducibility

The equation generator uses a fixed seed (`--seed 42`) so that the same
20,000 equations are produced on every run.  The pre-generated file
`equations_20000.txt` was created with:

```bash
python equation_generator.py -n 20000 --min-val -1 --max-val 1 \
    --min-len 3 --max-len 203 --seed 42 -o equations_20000.txt
```

---

## Limitations

As discussed in the Threats to Validity section of the paper:

- Timing figures are single-run wall-clock measurements and are
  susceptible to platform load; they are indicative, not statistically
  robust.
- The STD calculator processes fewer equations than DBZ (it aborts on
  DBZ expressions), making throughput comparison asymmetric.
- Operands are restricted to integers in `[-1, 1]` to maximise
  division-by-zero frequency.

---

## Citation

```
P. Jean-Paul and S. Wahid, "A Proof-of-Concept Division-by-Zero
Calculator Using Semi-structured Complex Numbers," 2024.
```
