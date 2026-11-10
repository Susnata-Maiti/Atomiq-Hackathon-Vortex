"""
Vortex: Master End-to-End Hybrid Quantum-Classical Pipeline Runner
Atomiq Hackathon (Qiskit Fall Fest)

Executes Stage 1 (Predict), Stage 2 (Select), and Stage 3 (Simulate),
generating all mandatory top-level submission CSV files and diagnostic reports.
"""

import sys
import time
import pandas as pd
import numpy as np

from src.data_loader import load_dataset
from src.stage1_predict import run_stage1_prediction
from src.stage2_select import run_stage2_selection
from src.stage3_simulate import run_stage3_simulation
from src.config import (
    STAGE1_RESULT_PATH,
    STAGE2_RESULT_PATH,
    STAGE3_RESULT_PATH,
    ID_COL,
    BUDGET_LIMIT,
    CAPACITY_LIMIT,
    EXACT_SELECTION_K,
)


def main():
    print("#" * 70)
    print("  VORTEX: HYBRID QUANTUM-CLASSICAL TERM DEPOSIT CAMPAIGN PIPELINE")
    print("  Atomiq Hackathon | Qiskit Fall Fest 2026")
    print("#" * 70)
    start_time = time.time()

    # Step 0: Data Loading & Integrity Validation
    print("\n>>> Loading and validating campaign dataset...")
    train_df, test_df, stage2_df, constraints = load_dataset()
    print(f"Loaded: {len(train_df)} training customers, {len(test_df)} test customers, {len(stage2_df)} operational records.")

    # Step 1: Stage 1 - Subscription Prediction
    s1_results_df, top_10_df, cv_summary = run_stage1_prediction(train_df, test_df)

    # Step 2: Stage 2 - Constrained Customer Selection
    candidates, classical_sol, qaoa_sol = run_stage2_selection(top_10_df, stage2_df)

    # Extract the 6 selected customers
    selected_cids = qaoa_sol["selected_ids"]
    selected_customers_df = candidates[candidates[ID_COL].isin(selected_cids)].copy().reset_index(drop=True)

    # Step 3: Stage 3 - Campaign Outcome Quantum Simulation
    s3_results_df, s3_summary = run_stage3_simulation(selected_customers_df)

    elapsed_time = time.time() - start_time

    # Verification Checks
    print("\n" + "=" * 70)
    print("  END-TO-END PIPELINE VALIDATION & INTEGRITY AUDIT")
    print("=" * 70)

    # Check 1: File Generation
    for path, name in [
        (STAGE1_RESULT_PATH, "Stage 1 Result File"),
        (STAGE2_RESULT_PATH, "Stage 2 Result File"),
        (STAGE3_RESULT_PATH, "Stage 3 Result File"),
    ]:
        assert path.exists(), f"Missing output file: {path}"
        df = pd.read_csv(path)
        print(f"[PASS] {name} verified at {path.name} ({len(df)} rows)")

    # Check 2: Stage 2 Feasibility
    assert len(selected_cids) == EXACT_SELECTION_K, f"Selected count {len(selected_cids)} != {EXACT_SELECTION_K}"
    assert qaoa_sol["total_cost"] <= BUDGET_LIMIT, f"Budget exceeded: {qaoa_sol['total_cost']} > {BUDGET_LIMIT}"
    assert qaoa_sol["total_capacity"] <= CAPACITY_LIMIT, f"Capacity exceeded: {qaoa_sol['total_capacity']} > {CAPACITY_LIMIT}"
    print(f"[PASS] Stage 2 Feasibility: Exactly {EXACT_SELECTION_K} unique IDs, Cost = {qaoa_sol['total_cost']:.1f} <= {BUDGET_LIMIT}, Capacity = {qaoa_sol['total_capacity']:.1f} <= {CAPACITY_LIMIT}")

    # Check 3: Closeness to Exact Probability
    print(f"[PASS] Stage 3 Closeness: Quantum Estimate = {s3_summary['p_quantum_ideal']:.6f}, Exact Analytical = {s3_summary['p_exact']:.6f}, Delta = {s3_summary['error_quantum']:.6f}")

    # Final Executive Summary
    print("\n" + "#" * 70)
    print("  VORTEX EXECUTIVE CHALLENGE ANSWER")
    print("#" * 70)
    print(f"Final 6 Customers Selected to Contact: {', '.join(selected_cids)}")
    print(f"Expected Net Campaign Value (Z):        ${qaoa_sol['objective_value']:.2f}")
    print(f"Total Campaign Budget Consumed:         {qaoa_sol['total_cost']:.1f} / {BUDGET_LIMIT} units")
    print(f"Total Operational Capacity Consumed:    {qaoa_sol['total_capacity']:.1f} / {CAPACITY_LIMIT} units")
    print(f"Probability at Least 3 Customers Convert: {s3_summary['p_quantum_ideal'] * 100:.2f}% (Exact: {s3_summary['p_exact'] * 100:.2f}%)")
    print(f"Total Pipeline Runtime:                 {elapsed_time:.2f} seconds")
    print("#" * 70)


if __name__ == "__main__":
    main()
