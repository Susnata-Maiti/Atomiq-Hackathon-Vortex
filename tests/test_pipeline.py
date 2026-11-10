"""
Comprehensive Validation Tests for Vortex
Verifies schema compliance, feasibility constraints, and numerical accuracy.
"""

import pytest
import pandas as pd
import numpy as np

from src.data_loader import load_dataset
from src.config import (
    STAGE1_RESULT_PATH,
    STAGE2_RESULT_PATH,
    STAGE3_RESULT_PATH,
    BUDGET_LIMIT,
    CAPACITY_LIMIT,
    EXACT_SELECTION_K,
    CANDIDATE_POOL_SIZE,
    STAGE3_QUBITS,
    SUCCESS_THRESHOLD,
    ID_COL,
)
from src.stage3_simulate import compute_exact_poisson_binomial


def test_data_loading():
    """Validates sheet loading, sample counts, and customer ID alignment."""
    train_df, test_df, stage2_df, constraints = load_dataset()
    assert len(train_df) == 300
    assert len(test_df) == 100
    assert len(stage2_df) == 400
    assert ID_COL in test_df.columns
    # Ensure no customer_id overlap between train and test
    overlap = set(train_df[ID_COL]) & set(test_df[ID_COL])
    assert len(overlap) == 0, f"Found overlapping customer IDs: {overlap}"


def test_stage1_output_format():
    """Validates stage1_result.csv format, bounds, and ranking integrity."""
    assert STAGE1_RESULT_PATH.exists(), "stage1_result.csv missing"
    df = pd.read_csv(STAGE1_RESULT_PATH)
    assert len(df) == 100, f"Expected 100 rows, got {len(df)}"
    for col in [ID_COL, "predicted_probability", "rank", "top_10"]:
        assert col in df.columns, f"Missing column {col} in stage1_result.csv"

    # Probabilities in [0, 1]
    assert (df["predicted_probability"] >= 0.0).all()
    assert (df["predicted_probability"] <= 1.0).all()

    # Ranks strictly 1..100
    assert list(df["rank"]) == list(range(1, 101))

    # Exactly 10 top_10 flags
    assert df["top_10"].sum() == CANDIDATE_POOL_SIZE


def test_stage2_feasibility_and_optimality():
    """Validates Stage 2 budget, capacity, cardinality, and gap to optimum."""
    assert STAGE2_RESULT_PATH.exists(), "stage2_result.csv missing"
    df = pd.read_csv(STAGE2_RESULT_PATH)
    assert len(df) == CANDIDATE_POOL_SIZE

    selected = df[df["selected_in_stage2"]]
    assert len(selected) == EXACT_SELECTION_K, f"Selected {len(selected)} != {EXACT_SELECTION_K}"

    total_cost = selected["contact_cost"].sum()
    total_cap = selected["capacity_units"].sum()
    assert total_cost <= BUDGET_LIMIT, f"Budget exceeded: {total_cost} > {BUDGET_LIMIT}"
    assert total_cap <= CAPACITY_LIMIT, f"Capacity exceeded: {total_cap} > {CAPACITY_LIMIT}"

    # Verify gap to optimum is non-negative and near zero
    gap = df["gap_to_optimum"].iloc[0]
    assert gap >= -1e-5, f"Negative optimality gap: {gap}"
    assert gap <= 2.0, f"Optimality gap too large: {gap}"


def test_stage3_simulation_validity():
    """Validates Stage 3 quantum amplitude encoding and statistical accuracy."""
    assert STAGE3_RESULT_PATH.exists(), "stage3_result.csv missing"
    df = pd.read_csv(STAGE3_RESULT_PATH)
    assert len(df) == STAGE3_QUBITS

    # Angles theta = 2 * arcsin(sqrt(p))
    for _, row in df.iterrows():
        p = row["predicted_probability"]
        theta = row["rotation_angle_rad"]
        expected_theta = 2.0 * np.arcsin(np.sqrt(p))
        assert abs(theta - expected_theta) < 1e-4

    p_exact = df["exact_analytical_probability"].iloc[0]
    p_quant = df["quantum_probability_estimate"].iloc[0]
    sigma = df["shot_noise_std_error"].iloc[0]

    assert 0.0 <= p_exact <= 1.0
    assert 0.0 <= p_quant <= 1.0
    # Quantum estimate must be within 3 sigma of exact solution
    assert abs(p_quant - p_exact) < 3.0 * sigma + 1e-4
