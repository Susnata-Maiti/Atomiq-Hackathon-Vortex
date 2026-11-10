"""
Stage 2: Constrained Customer Selection Module
Implements Exact Classical Brute-Force Benchmark, QUBO / Ising Formulation,
and QAOA (Quantum Approximate Optimization Algorithm) Solver.
"""

import numpy as np
import pandas as pd
from itertools import combinations
from typing import Dict, Any, Tuple, List
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

from .config import (
    CANDIDATE_POOL_SIZE,
    EXACT_SELECTION_K,
    BUDGET_LIMIT,
    CAPACITY_LIMIT,
    QAOA_P,
    QAOA_MAX_ITER,
    PENALTY_K,
    PENALTY_BUDGET,
    PENALTY_CAPACITY,
    SIMULATOR_SHOTS,
    SIMULATOR_SEED,
    OPTIMIZER_SEED,
    TRANSPILER_SEED,
    STAGE2_RESULT_PATH,
    ID_COL,
)


def solve_classical_exact(candidates_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Solves the exact constrained selection problem via brute-force enumeration
    over all binom(10, 6) = 210 candidate subsets.
    Guarantees the global theoretical optimum.
    """
    records = candidates_df.to_dict("records")
    best_val = -float("inf")
    best_combo = None

    valid_combos_count = 0
    all_combos_count = 0

    for combo in combinations(records, EXACT_SELECTION_K):
        all_combos_count += 1
        cost = sum(c["contact_cost"] for c in combo)
        cap = sum(c["capacity_units"] for c in combo)
        val = sum(c["expected_net_value"] for c in combo)

        if cost <= BUDGET_LIMIT and cap <= CAPACITY_LIMIT:
            valid_combos_count += 1
            if val > best_val:
                best_val = val
                best_combo = combo

    if best_combo is None:
        raise ValueError("No feasible combination found within budget and capacity limits!")

    selected_ids = [c[ID_COL] for c in best_combo]
    total_cost = sum(c["contact_cost"] for c in best_combo)
    total_cap = sum(c["capacity_units"] for c in best_combo)

    # Form bitstring for the top 10 order
    all_ids = candidates_df[ID_COL].tolist()
    bitstring = "".join(["1" if cid in selected_ids else "0" for cid in all_ids])

    return {
        "selected_ids": selected_ids,
        "objective_value": best_val,
        "total_cost": total_cost,
        "total_capacity": total_cap,
        "bitstring": bitstring,
        "valid_combos": valid_combos_count,
        "total_combos": all_combos_count,
    }


def build_qaoa_circuit(
    linear_coeffs: np.ndarray,
    quad_coeffs: np.ndarray,
    p: int = 2,
) -> Tuple[QuantumCircuit, ParameterVector, ParameterVector]:
    """
    Constructs a p-layer QAOA circuit for the 10-qubit Ising cost Hamiltonian.
    
    H_C = sum_i h_i Z_i + sum_{i < j} J_{ij} Z_i Z_j
    """
    n_qubits = len(linear_coeffs)
    qc = QuantumCircuit(n_qubits, n_qubits)

    gamma = ParameterVector("gamma", p)
    beta = ParameterVector("beta", p)

    # Initial state: Hadamard on all qubits (|+>^10)
    qc.h(range(n_qubits))

    for layer in range(p):
        # 1. Problem Hamiltonian evolution: e^{-i gamma H_C}
        # Two-qubit ZZ interactions
        for i in range(n_qubits):
            for j in range(i + 1, n_qubits):
                J_ij = quad_coeffs[i, j]
                if abs(J_ij) > 1e-6:
                    qc.rzz(2 * gamma[layer] * J_ij, i, j)

        # Single-qubit Z rotations
        for i in range(n_qubits):
            h_i = linear_coeffs[i]
            if abs(h_i) > 1e-6:
                qc.rz(2 * gamma[layer] * h_i, i)

        # 2. Mixer Hamiltonian evolution: e^{-i beta H_M} (Transverse field X)
        for i in range(n_qubits):
            qc.rx(2 * beta[layer], i)

    # Measurement
    qc.measure(range(n_qubits), range(n_qubits))
    return qc, gamma, beta


def run_stage2_selection(
    top_10_df: pd.DataFrame,
    stage2_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Executes Stage 2:
    - Merges Stage 1 top 10 with Stage 2 operational data
    - Computes expected net value
    - Runs exact classical brute-force solver (benchmark)
    - Formulates QUBO / Ising and executes QAOA quantum optimizer
    - Evaluates gap, best bitstrings, and feasibility
    - Generates stage2_result.csv
    """
    print("=" * 60)
    print("STAGE 2: CONSTRAINED CUSTOMER SELECTION & QAOA OPTIMIZATION")
    print("=" * 60)

    # 1. Prepare candidates data
    candidates = top_10_df[[ID_COL, "predicted_probability"]].merge(
        stage2_df, on=ID_COL, how="left"
    )

    # Calculate Expected Net Value: V = P * expected_deposit_value - contact_cost
    candidates["expected_net_value"] = (
        candidates["predicted_probability"] * candidates["expected_deposit_value"]
        - candidates["contact_cost"]
    )

    print("\n--- Candidate Pool (N=10) Operational Parameters ---")
    print(
        f"{'Index':<5} | {'ID':<6} | {'Prob':<7} | {'Cost':<5} | {'DepVal':<6} | {'CapUnits':<8} | {'ExpNetVal':<10}"
    )
    print("-" * 65)
    for idx, r in candidates.iterrows():
        print(
            f"{idx:<5} | {r[ID_COL]:<6} | {r['predicted_probability']:<7.4f} | "
            f"{int(r['contact_cost']):<5} | {int(r['expected_deposit_value']):<6} | "
            f"{int(r['capacity_units']):<8} | {r['expected_net_value']:<10.4f}"
        )

    # 2. Solve Classical Exact Optimum
    print("\nSolving Exact Classical Benchmark (Enumerating 210 combinations)...")
    classical_sol = solve_classical_exact(candidates)
    print(f"Classical Global Optimum Objective: {classical_sol['objective_value']:.6f}")
    print(f"Selected IDs: {classical_sol['selected_ids']}")
    print(
        f"Total Cost: {classical_sol['total_cost']:.1f} / {BUDGET_LIMIT} | "
        f"Total Capacity: {classical_sol['total_capacity']:.1f} / {CAPACITY_LIMIT}"
    )
    print(f"Classical Bitstring (q0..q9): {classical_sol['bitstring']}")

    # 3. Formulate QUBO and Ising Hamiltonian for QAOA
    v = candidates["expected_net_value"].values
    c = candidates["contact_cost"].values
    h = candidates["capacity_units"].values
    n = len(candidates)

    # QUBO objective to minimize:
    # Q(x) = -sum v_i x_i + P_k (sum x_i - 6)^2 + P_c (sum c_i x_i - 25)^2_penalty
    # Expanding (sum x_i - 6)^2 = -11 sum x_i + 2 sum_{i<j} x_i x_j + 36
    # Mapping to Ising: x_i = (1 - Z_i)/2
    # Z_i = 1 - 2 x_i

    # Construct linear and quadratic Ising coefficients
    linear_h = np.zeros(n)
    quad_J = np.zeros((n, n))

    # Base objective: - v_i x_i
    for i in range(n):
        linear_h[i] += 0.5 * v[i]

    # Cardinality penalty: P_k * (sum x_i - K)^2
    # in terms of Z: sum x_i = n/2 - 0.5 sum Z_i
    # (n/2 - 0.5 sum Z_i - K)^2 = const - (n - 2K)/2 sum Z_i + 0.25 (sum Z_i)^2
    # (sum Z_i)^2 = n + 2 sum_{i<j} Z_i Z_j
    for i in range(n):
        linear_h[i] += PENALTY_K * (-(n - 2 * EXACT_SELECTION_K) / 2.0)
    for i in range(n):
        for j in range(i + 1, n):
            quad_J[i, j] += PENALTY_K * 0.5

    # Capacity and budget linear guidance
    for i in range(n):
        linear_h[i] += PENALTY_BUDGET * (c[i] / 5.0)
        linear_h[i] += PENALTY_CAPACITY * (h[i] / 5.0)

    # 4. QAOA Circuit and Optimization
    print(f"\nBuilding {QAOA_P}-layer QAOA Circuit on 10 qubits...")
    qaoa_circuit, gamma_params, beta_params = build_qaoa_circuit(linear_h, quad_J, p=QAOA_P)
    simulator = AerSimulator()

    def qaoa_energy_objective(params: np.ndarray) -> float:
        gammas = params[:QAOA_P]
        betas = params[QAOA_P:]

        param_dict = {}
        for l in range(QAOA_P):
            param_dict[gamma_params[l]] = gammas[l]
            param_dict[beta_params[l]] = betas[l]

        bound_qc = qaoa_circuit.assign_parameters(param_dict)
        t_qc = transpile(bound_qc, simulator, seed_transpiler=TRANSPILER_SEED)
        job = simulator.run(t_qc, shots=2048, seed_simulator=SIMULATOR_SEED)
        counts = job.result().get_counts()

        total_energy = 0.0
        total_shots = 2048
        for bstr, count in counts.items():
            # Qiskit bitstring order is q_{n-1} ... q_0
            bits = [int(bstr[-(i + 1)]) for i in range(n)]
            # Energy calculation
            val = np.sum(v * bits)
            k_sum = np.sum(bits)
            cost_sum = np.sum(c * bits)
            cap_sum = np.sum(h * bits)

            pen_k = PENALTY_K * ((k_sum - EXACT_SELECTION_K) ** 2)
            pen_cost = PENALTY_BUDGET * ((max(0, cost_sum - BUDGET_LIMIT)) ** 2)
            pen_cap = PENALTY_CAPACITY * ((max(0, cap_sum - CAPACITY_LIMIT)) ** 2)
            e = -val + pen_k + pen_cost + pen_cap
            total_energy += e * count

        return total_energy / total_shots

    # Optimize QAOA parameters using COBYLA
    np.random.seed(OPTIMIZER_SEED)
    initial_params = np.random.uniform(0.1, 0.8, 2 * QAOA_P)

    print("Optimizing QAOA parameters with COBYLA...")
    opt_res = minimize(
        qaoa_energy_objective,
        initial_params,
        method="COBYLA",
        options={"maxiter": QAOA_MAX_ITER, "disp": False},
    )

    opt_gammas = opt_res.x[:QAOA_P]
    opt_betas = opt_res.x[QAOA_P:]
    print(f"QAOA Optimization Complete. Optimal Gammas: {opt_gammas.round(4)}, Betas: {opt_betas.round(4)}")

    # 5. Full Sampling from Optimal QAOA Circuit
    print(f"\nSampling {SIMULATOR_SHOTS} shots from optimal QAOA circuit...")
    param_dict = {}
    for l in range(QAOA_P):
        param_dict[gamma_params[l]] = opt_gammas[l]
        param_dict[beta_params[l]] = opt_betas[l]

    final_bound_qc = qaoa_circuit.assign_parameters(param_dict)
    t_final_qc = transpile(final_bound_qc, simulator, seed_transpiler=TRANSPILER_SEED)
    job = simulator.run(t_final_qc, shots=SIMULATOR_SHOTS, seed_simulator=SIMULATOR_SEED)
    counts = job.result().get_counts()

    # Decode bitstrings into candidate selections
    bitstring_evals = []
    for bstr, count in counts.items():
        # Bits in q0..q9 order
        bits = [int(bstr[-(i + 1)]) for i in range(n)]
        k_sum = sum(bits)
        cost_sum = sum(c[i] * bits[i] for i in range(n))
        cap_sum = sum(h[i] * bits[i] for i in range(n))
        val = sum(v[i] * bits[i] for i in range(n))

        is_feasible = (
            (k_sum == EXACT_SELECTION_K)
            and (cost_sum <= BUDGET_LIMIT)
            and (cap_sum <= CAPACITY_LIMIT)
        )

        bitstring_evals.append({
            "bitstring": "".join(map(str, bits)),
            "shots": count,
            "k_sum": k_sum,
            "cost": cost_sum,
            "capacity": cap_sum,
            "objective_value": val,
            "is_feasible": is_feasible,
        })

    eval_df = pd.DataFrame(bitstring_evals).sort_values(
        by=["is_feasible", "objective_value", "shots"], ascending=[False, False, False]
    ).reset_index(drop=True)

    feasible_df = eval_df[eval_df["is_feasible"]].reset_index(drop=True)
    best_qaoa_row = feasible_df.iloc[0] if len(feasible_df) > 0 else eval_df.iloc[0]

    # Selected customer IDs from best bitstring
    best_bits = [int(b) for b in best_qaoa_row["bitstring"]]
    qaoa_selected_ids = [candidates.iloc[i][ID_COL] for i in range(n) if best_bits[i] == 1]

    gap_to_optimum = classical_sol["objective_value"] - best_qaoa_row["objective_value"]

    qaoa_sol = {
        "selected_ids": qaoa_selected_ids,
        "objective_value": best_qaoa_row["objective_value"],
        "total_cost": best_qaoa_row["cost"],
        "total_capacity": best_qaoa_row["capacity"],
        "bitstring": best_qaoa_row["bitstring"],
        "shots_count": int(best_qaoa_row["shots"]),
        "gap_to_optimum": gap_to_optimum,
        "optimal_gammas": opt_gammas.tolist(),
        "optimal_betas": opt_betas.tolist(),
        "top_bitstrings": feasible_df.head(5).to_dict("records"),
    }

    print("\n--- QAOA Solution Summary ---")
    print(f"QAOA Selected IDs: {qaoa_sol['selected_ids']}")
    print(f"QAOA Objective Value: {qaoa_sol['objective_value']:.6f}")
    print(f"Classical Exact Optimum: {classical_sol['objective_value']:.6f}")
    print(f"Optimality Gap: {gap_to_optimum:.6f}")
    print(
        f"Total Cost: {qaoa_sol['total_cost']:.1f} / {BUDGET_LIMIT} | "
        f"Total Capacity: {qaoa_sol['total_capacity']:.1f} / {CAPACITY_LIMIT}"
    )

    # 6. Export required stage2_result.csv format
    # The specification requires: top 10 IDs with their inputs, six selected IDs,
    # budget and capacity totals, objective value, best bitstrings, classical optimum, and gap to it.
    out_rows = []
    for idx, r in candidates.iterrows():
        is_selected = r[ID_COL] in qaoa_sol["selected_ids"]
        out_rows.append({
            ID_COL: r[ID_COL],
            "predicted_probability": r["predicted_probability"],
            "expected_deposit_value": r["expected_deposit_value"],
            "contact_cost": r["contact_cost"],
            "capacity_units": r["capacity_units"],
            "expected_net_value": r["expected_net_value"],
            "selected_in_stage2": is_selected,
            "qaoa_objective_value": qaoa_sol["objective_value"],
            "classical_optimum": classical_sol["objective_value"],
            "gap_to_optimum": gap_to_optimum,
            "total_budget_used": qaoa_sol["total_cost"],
            "budget_limit": BUDGET_LIMIT,
            "total_capacity_used": qaoa_sol["total_capacity"],
            "capacity_limit": CAPACITY_LIMIT,
            "best_bitstring": qaoa_sol["bitstring"],
        })

    s2_result_df = pd.DataFrame(out_rows)
    s2_result_df.to_csv(STAGE2_RESULT_PATH, index=False)
    print(f"\n[OK] Successfully generated {STAGE2_RESULT_PATH} with candidate selection.")

    return candidates, classical_sol, qaoa_sol
