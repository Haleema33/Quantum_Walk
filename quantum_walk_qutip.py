"""
Quantum Search Using a Discrete-Time Quantum Walk on a 1D Cycle
================================================================
Single-framework implementation for the Group 7 research proposal.

Quantum simulation framework: QuTiP
Visualization: Matplotlib
Classical baseline: standard Python random module

This file implements the proposal's core experimental work:
- 1D cycle/ring with periodic boundary conditions
- position Hilbert space + two-state coin Hilbert space
- uniform initial superposition
- Hadamard coin
- conditional left/right shift
- marked-position phase-flip oracle
- repeated discrete-time quantum-walk evolution
- success probability P_success(t)
- P_max and t_max
- N = 8, 16, 32, 64, 128
- normalization and unitarity checks
- periodic-boundary checks
- classical random-walk comparison
- six proposal result plots
- CSV summary of numerical results

Install:
    pip install qutip matplotlib

Run:
    python quantum_walk_qutip_complete.py

Outputs:
    results/
        01_initial_probability_N8.png
        02_quantum_distribution_N8.png
        03_success_probability_N8.png
        04_pmax_vs_N.png
        05_tmax_vs_N.png
        06_quantum_vs_classical.png
        results_summary.csv

IMPORTANT MODEL CHOICE
----------------------
The proposal contains both DTQW language and Grover-diffusion discussion.
This implementation follows the project's main title/objectives and uses
a proper COINED DISCRETE-TIME QUANTUM WALK on a 1D cycle.

One search-walk step is defined as:

    Oracle -> Coin -> Conditional Shift

The oracle marks the target only by a phase flip. It does not directly
increase probability. Any target-probability change comes from later
interference produced by the coin and shift dynamics.

To start first install using command in terminal:
    "pip install qutip matplotlib"
and then run the script using:
    "python quantum_walk_qutip_complete.py"
"""

from pathlib import Path
import csv
import math
import random

import matplotlib.pyplot as plt
from qutip import Qobj, basis, qeye, tensor


# ============================================================
# USER / EXPERIMENT SETTINGS
# ============================================================

SYSTEM_SIZES = [8, 16, 32, 64, 128]

# Target is chosen at approximately 3/8 of the cycle.
# Therefore N=8 -> target=3.
TARGET_FRACTION = 3 / 8

# Number of quantum steps tested for each N.
# N=8 -> 32 steps, N=16 -> 64 steps, etc.
STEP_MULTIPLIER = 4

# Monte-Carlo runs for the classical random walk.
CLASSICAL_TRIALS = 3000

RANDOM_SEED = 42

# Numerical tolerance for validation.
TOL = 1e-10

OUTPUT_DIR = Path("results")


# ============================================================
# BASIC QUANTUM STATES
# ============================================================

LEFT = basis(2, 0)
RIGHT = basis(2, 1)


def hadamard_coin():
    """
    2-state Hadamard coin:

        H = 1/sqrt(2) [[1, 1],
                       [1,-1]]

    It mixes LEFT and RIGHT amplitudes.
    """
    return Qobj(
        [
            [1 / math.sqrt(2), 1 / math.sqrt(2)],
            [1 / math.sqrt(2), -1 / math.sqrt(2)],
        ]
    )


# ============================================================
# INITIAL STATE
# ============================================================

def uniform_position_state(n):
    """
    Uniform superposition across all N positions:

        |p> = 1/sqrt(N) sum_x |x>
    """
    state = 0 * basis(n, 0)

    for x in range(n):
        state += basis(n, x)

    return state.unit()


def balanced_coin_state():
    """
    Balanced coin state.

    We use:
        (|L> + i|R>) / sqrt(2)

    The relative phase i avoids an artificial left/right bias that can
    arise for some real-valued starting coin states with a Hadamard walk.
    """
    return (LEFT + 1j * RIGHT).unit()


def initial_state(n):
    """
    Composite initial state:

        |psi_0> = |uniform position> tensor |balanced coin>

    This gives equal initial position probabilities P(x)=1/N.
    """
    return tensor(
        uniform_position_state(n),
        balanced_coin_state(),
    )


# ============================================================
# QUANTUM OPERATORS
# ============================================================

def full_coin_operator(n):
    """
    Apply the Hadamard only to the coin subsystem:

        C = I_position tensor H_coin
    """
    return tensor(qeye(n), hadamard_coin())


def oracle_operator(n, target):
    """
    Mark the target position with a phase flip.

    Position oracle:
        O_p = I - 2|target><target|

    Full operator:
        O = O_p tensor I_coin

    Both LEFT and RIGHT components at the target get phase -1.
    """
    target_projector = basis(n, target) * basis(n, target).dag()

    position_oracle = qeye(n) - 2 * target_projector

    return tensor(position_oracle, qeye(2))


def conditional_shift_operator(n):
    """
    Conditional shift on a cycle.

    LEFT:
        |x,L> -> |x-1 mod N,L>

    RIGHT:
        |x,R> -> |x+1 mod N,R>

    The modulo operation creates periodic boundary conditions.
    """
    shift = 0 * tensor(qeye(n), qeye(2))

    left_projector = LEFT * LEFT.dag()
    right_projector = RIGHT * RIGHT.dag()

    for x in range(n):
        ket_left_destination = basis(n, (x - 1) % n)
        bra_source = basis(n, x).dag()

        shift += tensor(
            ket_left_destination * bra_source,
            left_projector,
        )

        ket_right_destination = basis(n, (x + 1) % n)

        shift += tensor(
            ket_right_destination * bra_source,
            right_projector,
        )

    return shift


# ============================================================
# PROBABILITY MEASUREMENT
# ============================================================

def position_probability(state, n, x):
    """
    Probability that the walker is at position x,
    regardless of its LEFT/RIGHT coin value.
    """
    projector = tensor(
        basis(n, x) * basis(n, x).dag(),
        qeye(2),
    )

    value = state.dag() * projector * state

    # QuTiP versions may return either a scalar or 1x1 Qobj here.
    if hasattr(value, "full"):
        value = value.full()[0, 0]

    return float(value.real)


def probability_distribution(state, n):
    """
    Return P(x) for x = 0,...,N-1.
    """
    return [
        position_probability(state, n, x)
        for x in range(n)
    ]


# ============================================================
# QUANTUM-WALK SIMULATION
# ============================================================

def run_quantum_search(n, target, steps):
    """
    Run the complete DTQW search experiment.

    One step:
        1. oracle
        2. Hadamard coin
        3. conditional shift

    Records:
        - probability distribution after every step
        - P_success(t)
        - normalization
        - P_max
        - t_max
    """
    psi = initial_state(n)

    oracle = oracle_operator(n, target)
    coin = full_coin_operator(n)
    shift = conditional_shift_operator(n)

    initial_probs = probability_distribution(psi, n)

    success_history = []
    normalization_history = []
    distributions = []

    for _ in range(steps):
        psi = oracle * psi
        psi = coin * psi
        psi = shift * psi

        probs = probability_distribution(psi, n)

        distributions.append(probs)
        success_history.append(probs[target])
        normalization_history.append(sum(probs))

    p_max = max(success_history)
    t_max = success_history.index(p_max) + 1

    return {
        "n": n,
        "target": target,
        "steps": steps,
        "state": psi,
        "initial_probs": initial_probs,
        "final_probs": distributions[-1],
        "distributions": distributions,
        "success_history": success_history,
        "normalization_history": normalization_history,
        "P_max": p_max,
        "t_max": t_max,
        "oracle": oracle,
        "coin": coin,
        "shift": shift,
    }


# ============================================================
# VALIDATION TESTS
# ============================================================

def is_unitary(operator):
    """
    Check U^dagger U = I.
    """
    identity = qeye(operator.shape[0])
    identity.dims = operator.dims

    difference = operator.dag() * operator - identity

    return difference.norm() < TOL


def validate_model(n=8, target=3):
    """
    Required checks from the proposal:
    - initial normalization
    - oracle unitary
    - coin unitary
    - shift unitary
    - oracle preserves probability
    - cycle boundary conditions work
    """
    print("\n" + "=" * 72)
    print("MODEL VALIDATION")
    print("=" * 72)

    psi = initial_state(n)

    oracle = oracle_operator(n, target)
    coin = full_coin_operator(n)
    shift = conditional_shift_operator(n)

    initial_norm = abs(float(psi.norm()) - 1.0) < TOL

    oracle_unitary = is_unitary(oracle)
    coin_unitary = is_unitary(coin)
    shift_unitary = is_unitary(shift)

    # Oracle should alter phase but preserve total probability.
    psi_after_oracle = oracle * psi
    oracle_preserves_norm = abs(float(psi_after_oracle.norm()) - 1.0) < TOL

    # Boundary test: |0,L> -> |N-1,L>
    start_left = tensor(basis(n, 0), LEFT)
    after_left = shift * start_left
    expected_left = tensor(basis(n, n - 1), LEFT)

    left_boundary = (
        abs(expected_left.overlap(after_left)) > 1 - TOL
    )

    # Boundary test: |N-1,R> -> |0,R>
    start_right = tensor(basis(n, n - 1), RIGHT)
    after_right = shift * start_right
    expected_right = tensor(basis(n, 0), RIGHT)

    right_boundary = (
        abs(expected_right.overlap(after_right)) > 1 - TOL
    )

    checks = {
        "Initial state normalized": initial_norm,
        "Oracle is unitary": oracle_unitary,
        "Coin is unitary": coin_unitary,
        "Shift is unitary": shift_unitary,
        "Oracle preserves normalization": oracle_preserves_norm,
        "LEFT boundary 0 -> N-1": left_boundary,
        "RIGHT boundary N-1 -> 0": right_boundary,
    }

    for name, status in checks.items():
        print(f"{name:<36}: {status}")

    if not all(checks.values()):
        raise RuntimeError(
            "Validation failed. Fix the model before trusting results."
        )

    print("All validation checks passed.")


# ============================================================
# CLASSICAL RANDOM-WALK BASELINE
# ============================================================

def classical_hitting_time(
    n,
    target,
    trials=CLASSICAL_TRIALS,
    seed=RANDOM_SEED,
):
    """
    Classical 1D random walk on the same cycle.

    Start position: 0

    At every step:
        LEFT  with probability 1/2
        RIGHT with probability 1/2

    We record how many steps are needed to first hit the target and return
    the average across many trials.
    """
    if target == 0:
        return 0.0

    rng = random.Random(seed)

    # A generous cutoff. Classical cycle hitting times scale around N^2.
    max_steps = 20 * n * n

    hitting_times = []

    for _ in range(trials):
        position = 0

        for step in range(1, max_steps + 1):
            move = -1 if rng.random() < 0.5 else 1

            position = (position + move) % n

            if position == target:
                hitting_times.append(step)
                break
        else:
            hitting_times.append(max_steps)

    return sum(hitting_times) / len(hitting_times)


# ============================================================
# PLOTS REQUIRED BY THE PROPOSAL
# ============================================================

def save_all_plots(results):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Use N=8 as the small demonstration system.
    demo = results[8]

    positions = list(range(8))

    # --------------------------------------------------------
    # 1. Initial probability distribution
    # --------------------------------------------------------
    plt.figure(figsize=(9, 5))
    plt.bar(positions, demo["initial_probs"])
    plt.axvline(
        demo["target"],
        linestyle="--",
        label=f"Marked position = {demo['target']}",
    )
    plt.xlabel("Position x")
    plt.ylabel("Probability P(x)")
    plt.title("Initial Probability Distribution (N=8)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "01_initial_probability_N8.png",
        dpi=200,
    )
    plt.close()

    # --------------------------------------------------------
    # 2. Quantum-walk probability distribution
    #    We use the distribution at t_max, not an arbitrary final step.
    # --------------------------------------------------------
    best_distribution = demo["distributions"][demo["t_max"] - 1]

    plt.figure(figsize=(9, 5))
    plt.bar(positions, best_distribution)
    plt.axvline(
        demo["target"],
        linestyle="--",
        label=f"Marked position = {demo['target']}",
    )
    plt.xlabel("Position x")
    plt.ylabel("Probability P(x)")
    plt.title(
        f"Quantum-Walk Distribution at Best Measurement Time "
        f"(N=8, t={demo['t_max']})"
    )
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "02_quantum_distribution_N8.png",
        dpi=200,
    )
    plt.close()

    # --------------------------------------------------------
    # 3. Success probability vs quantum-walk steps
    # --------------------------------------------------------
    walk_steps = list(range(1, demo["steps"] + 1))

    plt.figure(figsize=(9, 5))
    plt.plot(
        walk_steps,
        demo["success_history"],
        label="P_success(t)",
    )
    plt.axhline(
        1 / 8,
        linestyle="--",
        label="Initial probability 1/N",
    )
    plt.scatter(
        [demo["t_max"]],
        [demo["P_max"]],
        label=(
            f"P_max={demo['P_max']:.4f}, "
            f"t_max={demo['t_max']}"
        ),
    )
    plt.xlabel("Number of quantum-walk steps t")
    plt.ylabel("Success probability P_success(t)")
    plt.title("Success Probability vs Quantum-Walk Steps (N=8)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "03_success_probability_N8.png",
        dpi=200,
    )
    plt.close()

    ns = sorted(results.keys())

    pmax_values = [
        results[n]["P_max"]
        for n in ns
    ]

    tmax_values = [
        results[n]["t_max"]
        for n in ns
    ]

    classical_values = [
        results[n]["classical_hitting_time"]
        for n in ns
    ]

    # --------------------------------------------------------
    # 4. Maximum success probability vs system size
    # --------------------------------------------------------
    plt.figure(figsize=(9, 5))
    plt.plot(ns, pmax_values, marker="o")
    plt.xlabel("Number of positions N")
    plt.ylabel("Maximum success probability P_max")
    plt.title("Maximum Success Probability vs System Size")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "04_pmax_vs_N.png",
        dpi=200,
    )
    plt.close()

    # --------------------------------------------------------
    # 5. Steps to maximum probability vs system size
    # --------------------------------------------------------
    plt.figure(figsize=(9, 5))
    plt.plot(ns, tmax_values, marker="o")
    plt.xlabel("Number of positions N")
    plt.ylabel("Steps to maximum probability t_max")
    plt.title("Steps to Maximum Probability vs System Size")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "05_tmax_vs_N.png",
        dpi=200,
    )
    plt.close()

    # --------------------------------------------------------
    # 6. Classical vs quantum search comparison
    # --------------------------------------------------------
    plt.figure(figsize=(9, 5))
    plt.plot(
        ns,
        tmax_values,
        marker="o",
        label="Quantum: t_max",
    )
    plt.plot(
        ns,
        classical_values,
        marker="o",
        label="Classical: mean hitting time",
    )
    plt.xlabel("System size N")
    plt.ylabel("Number of steps")
    plt.title("Classical vs Quantum Search Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "06_quantum_vs_classical.png",
        dpi=200,
    )
    plt.close()


# ============================================================
# CSV RESULTS
# ============================================================

def save_results_csv(results):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    path = OUTPUT_DIR / "results_summary.csv"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "N",
                "target",
                "steps_tested",
                "initial_target_probability",
                "P_max",
                "t_max",
                "classical_mean_hitting_time",
                "max_normalization_error",
            ]
        )

        for n in sorted(results.keys()):
            result = results[n]

            max_norm_error = max(
                abs(value - 1.0)
                for value in result["normalization_history"]
            )

            writer.writerow(
                [
                    n,
                    result["target"],
                    result["steps"],
                    1 / n,
                    result["P_max"],
                    result["t_max"],
                    result["classical_hitting_time"],
                    max_norm_error,
                ]
            )


# ============================================================
# INTERPRETATION
# ============================================================

def print_interpretation(results):
    print("\n" + "=" * 72)
    print("RESULT INTERPRETATION")
    print("=" * 72)

    print(
        "\nFor each N, compare P_max with the initial probability 1/N."
    )

    for n in sorted(results.keys()):
        result = results[n]

        initial_probability = 1 / n

        amplification = (
            result["P_max"] / initial_probability
            if initial_probability > 0
            else 0
        )

        print(
            f"N={n:>3} | "
            f"1/N={initial_probability:.6f} | "
            f"P_max={result['P_max']:.6f} | "
            f"t_max={result['t_max']:>4} | "
            f"amplification={amplification:.3f}x | "
            f"classical mean={result['classical_hitting_time']:.2f}"
        )

    print(
        "\nDo not claim a quadratic quantum speedup automatically. "
        "The proposal specifically says the observed 1D results should "
        "determine whether an advantage exists."
    )


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main():
    print("=" * 72)
    print("QUANTUM SEARCH USING A DISCRETE-TIME QUANTUM WALK")
    print("Framework: QuTiP")
    print("=" * 72)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # 1. Validate the model before doing experiments
    # --------------------------------------------------------
    validate_model(n=8, target=3)

    # --------------------------------------------------------
    # 2. Run all proposal system sizes
    # --------------------------------------------------------
    results = {}

    print("\n" + "=" * 72)
    print("MAIN EXPERIMENT")
    print("=" * 72)

    print(
        f"\n{'N':>6} "
        f"{'Target':>8} "
        f"{'Steps':>8} "
        f"{'1/N':>12} "
        f"{'P_max':>12} "
        f"{'t_max':>8} "
        f"{'Classical':>14}"
    )

    print("-" * 75)

    for index, n in enumerate(SYSTEM_SIZES):
        target = int(round(n * TARGET_FRACTION)) % n

        if target == 0:
            target = 1

        steps = STEP_MULTIPLIER * n

        quantum_result = run_quantum_search(
            n=n,
            target=target,
            steps=steps,
        )

        # Confirm normalization at every time step.
        max_norm_error = max(
            abs(value - 1.0)
            for value in quantum_result["normalization_history"]
        )

        if max_norm_error > 1e-8:
            raise RuntimeError(
                f"Normalization failed for N={n}. "
                f"Maximum error={max_norm_error}"
            )

        classical_mean = classical_hitting_time(
            n=n,
            target=target,
            trials=CLASSICAL_TRIALS,
            seed=RANDOM_SEED + index,
        )

        quantum_result["classical_hitting_time"] = classical_mean

        results[n] = quantum_result

        print(
            f"{n:>6} "
            f"{target:>8} "
            f"{steps:>8} "
            f"{1/n:>12.6f} "
            f"{quantum_result['P_max']:>12.6f} "
            f"{quantum_result['t_max']:>8} "
            f"{classical_mean:>14.2f}"
        )

    # --------------------------------------------------------
    # 3. Save all proposal outputs
    # --------------------------------------------------------
    save_all_plots(results)
    save_results_csv(results)
    print_interpretation(results)

    print("\n" + "=" * 72)
    print("EXPERIMENT COMPLETE")
    print("=" * 72)

    print(f"\nResults saved in: {OUTPUT_DIR.resolve()}")

    print(
        "\nGenerated files:\n"
        "  01_initial_probability_N8.png\n"
        "  02_quantum_distribution_N8.png\n"
        "  03_success_probability_N8.png\n"
        "  04_pmax_vs_N.png\n"
        "  05_tmax_vs_N.png\n"
        "  06_quantum_vs_classical.png\n"
        "  results_summary.csv"
    )


if __name__ == "__main__":
    main()
