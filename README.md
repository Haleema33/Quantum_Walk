# Quantum Search Using a Discrete-Time Quantum Walk on a 1D Cycle

This project implements a **Discrete-Time Quantum Walk (DTQW) search algorithm** on a one-dimensional cycle using **QuTiP**.

The simulation studies whether quantum interference can increase the probability of finding a marked target position compared with a classical random walk.

The implementation is based on the project:

**Quantum Search Using Discrete-Time Quantum Random Walks on a One-Dimensional Array**

---

## Project Overview

A quantum walker moves on a one-dimensional cycle containing `N` positions. The system contains a **position space** and a two-state **coin space** (`|0>` = Left, `|1>` = Right), so the total Hilbert-space dimension is `2N`.

The simulation tests:

```text
N = 8, 16, 32, 64, 128
```

## Framework Used

The main quantum simulation framework is **QuTiP**. It is used to create and evolve quantum states, position states, coin states, the Hadamard coin operator, the marked-position oracle, the conditional shift operator, and the tensor-product quantum system.

Matplotlib is used for plotting results, while a standard Python simulation is used for the classical random-walk baseline.

## Quantum Walk Algorithm

The initial walker is prepared in a uniform superposition over all positions, so initially:

```text
P(x) = 1 / N
```

For example, when `N = 8`:

```text
P(x) = 1 / 8 = 0.125
```

Each search step follows:

```text
Initial State
     |
     v
  Oracle
     |
     v
Hadamard Coin
     |
     v
Conditional Shift
     |
     v
Measure Probability
     |
     v
   Repeat
```

So one implemented step is:

```text
Oracle -> Coin -> Shift
```

## Initial State

The position state is initialized as a uniform superposition:

```text
|p> = 1/sqrt(N) * sum |x>
```

The coin is initialized in a balanced state, and the full state is:

```text
|psi> = |position> tensor |coin>
```

## Hadamard Coin

The Hadamard coin mixes the Left and Right amplitudes:

```text
        1
H = -------- [ 1   1 ]
     sqrt(2)  [ 1  -1 ]
```

## Conditional Shift

After applying the coin, the walker moves according to its coin state:

```text
|0> -> move Left
|1> -> move Right
```

For position `x`:

```text
Left:  x -> (x - 1) mod N
Right: x -> (x + 1) mod N
```

The modulo operation creates periodic boundary conditions. For `N = 8`:

```text
Moving Left from position 0 -> position 7
Moving Right from position 7 -> position 0
```

## Marked-Position Oracle

One position is selected as the target, for example:

```text
N = 8
Target = 3
```

The oracle marks the target by changing its phase:

```text
|target> -> -|target>
```

The oracle does **not** directly increase the target probability. Instead, the phase change influences later coin and shift operations and can produce constructive interference at the target.

## Success Probability

The main measured quantity is:

```text
P_success(t) = P(target, t)
```

The program records:

```text
P_max = highest observed target probability
t_max = step where P_max occurs
```

## Classical Random Walk

The project also includes a classical random-walk baseline. The walker starts at position `0` and moves Left or Right with probability `1/2` at each step.

The simulation records the average number of steps required to first reach the target. This is called the **classical mean hitting time**.

## Model Validation

Before the main experiment, the program checks:

```text
Initial state normalized
Oracle is unitary
Coin is unitary
Shift is unitary
Oracle preserves normalization
LEFT periodic boundary works
RIGHT periodic boundary works
```

A correct run should show all checks as `True`.

## Requirements

```text
Python 3.10+
QuTiP
Matplotlib
```

## Installation

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install qutip matplotlib
```

## Run the Project

Recommended structure:

```text
Quantum_Research/
|
|-- quantum_walk_qutip_complete.py
|-- README.md
```

Run:

```powershell
python quantum_walk_qutip_complete.py
```

## Example Result

A successful experiment may produce values like:

```text
N    Target   Steps      1/N       P_max     t_max     Classical
8       3       32     0.125000   0.281250     14       14.92
16      6       64     0.062500   0.149029     48       60.50
32     12      128     0.031250   0.075401     98      236.63
64     24      256     0.015625   0.035748    205      958.32
128    48      512     0.007812   0.020168    191     3804.41
```

For `N = 8`, the target probability increases from `0.125` to `0.28125`, which is about `2.25x` amplification.

## Generated Results

The program automatically creates:

```text
results/
|
|-- 01_initial_probability_N8.png
|-- 02_quantum_distribution_N8.png
|-- 03_success_probability_N8.png
|-- 04_pmax_vs_N.png
|-- 05_tmax_vs_N.png
|-- 06_quantum_vs_classical.png
`-- results_summary.csv
```

### Graph 1 — Initial Probability Distribution
Shows the equal starting probability across all positions.

### Graph 2 — Quantum-Walk Probability Distribution
Shows the probability distribution at `t_max`, the best measurement time.

### Graph 3 — Success Probability vs Steps
Shows `P_success(t)` and its oscillatory behavior, including the maximum `P_max`.

### Graph 4 — Maximum Success Probability vs System Size
Shows how `P_max` changes as `N` increases.

### Graph 5 — Steps to Maximum Probability vs System Size
Shows how `t_max` changes with system size.

### Graph 6 — Quantum vs Classical Search
Compares quantum `t_max` with the classical mean hitting time.

## CSV Results

`results_summary.csv` contains:

```text
N
Target
Steps tested
Initial target probability
P_max
t_max
Classical mean hitting time
Maximum normalization error
```

## Current Experimental Interpretation

The marked-position probability increases above its initial uniform value for the tested system sizes. However, `t_max` and classical hitting time are not identical performance measures, so the project should **not automatically claim a quadratic quantum speedup** from this comparison alone.

A safer conclusion is:

> The discrete-time quantum walk produces measurable target-probability amplification through quantum interference. The quantum and classical models show different scaling behaviour, but further analysis is required before claiming a formal quantum speedup.

## Is Grover's Algorithm Included?

No. The current implementation is a **Discrete-Time Quantum Walk search algorithm**.

It includes a Grover-like marked-state oracle because the target phase is flipped:

```text
|target> -> -|target>
```

However, it does **not** include the standard Grover diffusion operator.

The implemented loop is:

```text
Oracle -> Hadamard Coin -> Conditional Shift -> Repeat
```

Grover search can be added later as a separate comparison experiment if required.

## Main Research Question

> Can a discrete-time quantum walk on a one-dimensional cycle increase the probability of locating a marked position through quantum interference, and how does its behaviour compare with a classical random walk as the system size increases?

## Main Deliverables

- Working QuTiP DTQW simulation
- Marked-position oracle
- Hadamard coin
- Conditional shift
- Periodic boundary conditions
- Normalization and unitarity tests
- Success probability
- `P_max` and `t_max`
- Classical random-walk baseline
- Multiple system-size experiments
- Six research graphs
- CSV numerical results
- Classical-versus-quantum comparison

## Authors

Group 07 — Quantum Internship 2026

Project: **Quantum Search Using Discrete-Time Quantum Random Walks on a One-Dimensional Array**
