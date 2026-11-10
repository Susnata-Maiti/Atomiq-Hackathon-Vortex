"""
Vortex Pipeline Configuration and Reproducibility Parameters
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "bank_campaign_participant_release.xlsx"

STAGE1_RESULT_PATH = BASE_DIR / "stage1_result.csv"
STAGE2_RESULT_PATH = BASE_DIR / "stage2_result.csv"
STAGE3_RESULT_PATH = BASE_DIR / "stage3_result.csv"

# Global Reproducibility Seeds
RANDOM_SEED = 42
OPTIMIZER_SEED = 42
SIMULATOR_SEED = 42
TRANSPILER_SEED = 42
MONTE_CARLO_SEED = 42

# Stage 1 Parameters
CV_FOLDS = 5
NUMERICAL_COLS = ["age", "balance", "day", "campaign", "pdays", "previous"]
CATEGORICAL_COLS = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "poutcome",
]
TARGET_COL = "y"
ID_COL = "customer_id"

# Quantum Kernel Parameters
QUANTUM_KERNEL_N_QUBITS = 4
QUANTUM_KERNEL_REPS = 2

# Stage 2 Constraints
CANDIDATE_POOL_SIZE = 10  # N
EXACT_SELECTION_K = 6    # K
BUDGET_LIMIT = 25.0       # C
CAPACITY_LIMIT = 22.0     # H

# Stage 2 QAOA Parameters
QAOA_P = 2
QAOA_MAX_ITER = 150
PENALTY_K = 18.0
PENALTY_BUDGET = 2.5
PENALTY_CAPACITY = 2.5

# Stage 3 Simulation Parameters
STAGE3_QUBITS = 6
SUCCESS_THRESHOLD = 3     # At least 3 customers subscribe
SIMULATOR_SHOTS = 10000
MONTE_CARLO_TRIALS = 100000
