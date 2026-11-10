"""
Stage 1: Subscription Prediction Module
Implements Classical Calibrated Logistic Baseline, Quantum Kernel Classifier (QSVC),
Stratified 5-Fold Cross-Validation, and Generation of continuous probabilities for 100 test customers.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
)
from qiskit.circuit.library import ZZFeatureMap
from qiskit.quantum_info import Statevector

from .config import (
    RANDOM_SEED,
    CV_FOLDS,
    NUMERICAL_COLS,
    CATEGORICAL_COLS,
    TARGET_COL,
    ID_COL,
    STAGE1_RESULT_PATH,
    STAGE1_PREDICTIONS_PATH,
    STAGE1_PREDICTIONS_JSON,
    QUANTUM_KERNEL_N_QUBITS,
    QUANTUM_KERNEL_REPS,
)


def compute_quantum_kernel_matrix(
    X1: np.ndarray,
    X2: np.ndarray,
    n_qubits: int = 4,
    reps: int = 2,
) -> np.ndarray:
    """
    Computes the quantum fidelity kernel matrix K_ij = |<phi(x1_i)|phi(x2_j)>|^2
    using Qiskit's ZZFeatureMap and vectorized statevector overlaps.
    """
    fmap = ZZFeatureMap(n_qubits, reps=reps, entanglement="linear")

    # Generate statevectors for X1
    sv_list_1 = []
    for x in X1:
        qc = fmap.assign_parameters(x)
        sv = Statevector.from_instruction(qc).data
        sv_list_1.append(sv)
    V1 = np.array(sv_list_1)  # shape (N1, 2^n)

    # Generate statevectors for X2
    if X1 is X2:
        V2 = V1
    else:
        sv_list_2 = []
        for x in X2:
            qc = fmap.assign_parameters(x)
            sv = Statevector.from_instruction(qc).data
            sv_list_2.append(sv)
        V2 = np.array(sv_list_2)  # shape (N2, 2^n)

    # Overlap matrix: <psi_i | psi_j>
    overlap = V1 @ V2.conj().T
    kernel_matrix = np.abs(overlap) ** 2
    return np.clip(kernel_matrix, 0.0, 1.0)


def precision_recall_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int = 10) -> Tuple[float, float]:
    """Computes Precision@K and Recall@K."""
    order = np.argsort(y_score)[::-1]
    top_k_indices = order[:k]
    hits = np.sum(y_true[top_k_indices])
    total_positives = np.sum(y_true)
    precision_k = hits / k if k > 0 else 0.0
    recall_k = hits / total_positives if total_positives > 0 else 0.0
    return precision_k, recall_k


def run_stage1_prediction(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executes the Stage 1 pipeline:
    - Preprocessing and feature engineering strictly on train data
    - Stratified 5-Fold Cross Validation for Classical and Quantum classifiers
    - Generates continuous, well-calibrated subscription probabilities for all 100 test customers
    - Ranks customers descending by probability (tie-breaker: customer_id ascending)
    - Exports stage1_result.csv
    """
    print("=" * 60)
    print("STAGE 1: SUBSCRIPTION PREDICTION & QUANTUM-CLASSICAL MODELING")
    print("=" * 60)

    X_train_raw = train_df.drop(columns=[ID_COL, TARGET_COL])
    y_train = (train_df[TARGET_COL] == "yes").astype(int).values
    X_test_raw = test_df.drop(columns=[ID_COL])

    # 1. Classical Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_COLS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLS),
        ]
    )

    # Fit preprocessor on train only
    X_train_proc = preprocessor.fit_transform(X_train_raw)
    X_test_proc = preprocessor.transform(X_test_raw)

    # 2. Stratified Cross-Validation on Training Data
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)

    classical_metrics = {
        "roc_auc": [],
        "pr_auc": [],
        "precision@10": [],
        "recall@10": [],
        "brier_score": [],
        "log_loss": [],
    }

    qsvc_metrics = {
        "roc_auc": [],
        "pr_auc": [],
        "precision@10": [],
        "recall@10": [],
        "brier_score": [],
        "log_loss": [],
    }

    print(f"Running {CV_FOLDS}-Fold Stratified Cross-Validation strictly on training data...")

    for fold, (tr_idx, val_idx) in enumerate(skf.split(X_train_proc, y_train), 1):
        X_tr, X_val = X_train_proc[tr_idx], X_train_proc[val_idx]
        y_tr, y_val = y_train[tr_idx], y_train[val_idx]

        # --- Classical Calibrated Logistic Regression ---
        base_lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED)
        base_lr.fit(X_tr, y_tr)
        probs_val_lr = base_lr.predict_proba(X_val)[:, 1]

        p10_lr, r10_lr = precision_recall_at_k(y_val, probs_val_lr, k=10)
        classical_metrics["roc_auc"].append(roc_auc_score(y_val, probs_val_lr))
        classical_metrics["pr_auc"].append(average_precision_score(y_val, probs_val_lr))
        classical_metrics["precision@10"].append(p10_lr)
        classical_metrics["recall@10"].append(r10_lr)
        classical_metrics["brier_score"].append(brier_score_loss(y_val, probs_val_lr))
        classical_metrics["log_loss"].append(log_loss(y_val, probs_val_lr))

        # --- Quantum Kernel Classifier (QSVC) ---
        pca = PCA(n_components=QUANTUM_KERNEL_N_QUBITS, random_state=RANDOM_SEED)
        X_tr_pca = pca.fit_transform(X_tr)
        X_val_pca = pca.transform(X_val)

        # Scale to [0, pi] for angle encoding in ZZFeatureMap
        min_vals = X_tr_pca.min(axis=0)
        max_vals = X_tr_pca.max(axis=0)
        range_vals = np.where((max_vals - min_vals) > 1e-8, max_vals - min_vals, 1.0)

        X_tr_q = np.pi * (X_tr_pca - min_vals) / range_vals
        X_val_q = np.pi * (X_val_pca - min_vals) / range_vals

        # Compute quantum kernels
        K_tr = compute_quantum_kernel_matrix(X_tr_q, X_tr_q, n_qubits=QUANTUM_KERNEL_N_QUBITS, reps=QUANTUM_KERNEL_REPS)
        K_val = compute_quantum_kernel_matrix(X_val_q, X_tr_q, n_qubits=QUANTUM_KERNEL_N_QUBITS, reps=QUANTUM_KERNEL_REPS)

        svc = SVC(kernel="precomputed", class_weight="balanced", random_state=RANDOM_SEED)
        svc.fit(K_tr, y_tr)
        # Decision function with sigmoid calibration for continuous probabilities
        dec_tr = svc.decision_function(K_tr)
        dec_val = svc.decision_function(K_val)

        # Platt sigmoid calibration
        calibrator = LogisticRegression()
        calibrator.fit(dec_tr.reshape(-1, 1), y_tr)
        probs_val_qsvc = calibrator.predict_proba(dec_val.reshape(-1, 1))[:, 1]

        p10_q, r10_q = precision_recall_at_k(y_val, probs_val_qsvc, k=10)
        qsvc_metrics["roc_auc"].append(roc_auc_score(y_val, probs_val_qsvc))
        qsvc_metrics["pr_auc"].append(average_precision_score(y_val, probs_val_qsvc))
        qsvc_metrics["precision@10"].append(p10_q)
        qsvc_metrics["recall@10"].append(r10_q)
        qsvc_metrics["brier_score"].append(brier_score_loss(y_val, probs_val_qsvc))
        qsvc_metrics["log_loss"].append(log_loss(y_val, probs_val_qsvc))

    # Summarize CV metrics
    cv_summary = {
        "Classical_Logistic": {k: float(np.mean(v)) for k, v in classical_metrics.items()},
        "Quantum_Kernel_SVC": {k: float(np.mean(v)) for k, v in qsvc_metrics.items()},
    }

    print("\n--- 5-Fold Stratified Cross-Validation Results ---")
    print(f"{'Metric':<16} | {'Classical Baseline':<20} | {'Quantum Kernel Classifier':<25}")
    print("-" * 68)
    for m in ["roc_auc", "pr_auc", "precision@10", "recall@10", "brier_score", "log_loss"]:
        print(f"{m:<16} | {cv_summary['Classical_Logistic'][m]:<20.4f} | {cv_summary['Quantum_Kernel_SVC'][m]:<25.4f}")

    # 3. Train Final Models on Full 300 Training Records
    print("\nTraining final calibrated models on full 300 training records...")

    # Classical final model
    base_final_lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED)
    calibrated_lr_final = CalibratedClassifierCV(estimator=base_final_lr, method="sigmoid", cv=5)
    calibrated_lr_final.fit(X_train_proc, y_train)
    probs_test_lr = calibrated_lr_final.predict_proba(X_test_proc)[:, 1]

    # Quantum final model
    pca_final = PCA(n_components=QUANTUM_KERNEL_N_QUBITS, random_state=RANDOM_SEED)
    X_train_pca = pca_final.fit_transform(X_train_proc)
    X_test_pca = pca_final.transform(X_test_proc)

    min_vals = X_train_pca.min(axis=0)
    max_vals = X_train_pca.max(axis=0)
    range_vals = np.where((max_vals - min_vals) > 1e-8, max_vals - min_vals, 1.0)

    X_train_q = np.pi * (X_train_pca - min_vals) / range_vals
    X_test_q = np.pi * (X_test_pca - min_vals) / range_vals

    K_train_full = compute_quantum_kernel_matrix(X_train_q, X_train_q, n_qubits=QUANTUM_KERNEL_N_QUBITS, reps=QUANTUM_KERNEL_REPS)
    K_test_full = compute_quantum_kernel_matrix(X_test_q, X_train_q, n_qubits=QUANTUM_KERNEL_N_QUBITS, reps=QUANTUM_KERNEL_REPS)

    svc_final = SVC(kernel="precomputed", class_weight="balanced", random_state=RANDOM_SEED)
    svc_final.fit(K_train_full, y_train)

    dec_train_full = svc_final.decision_function(K_train_full)
    dec_test_full = svc_final.decision_function(K_test_full)

    calibrator_q = LogisticRegression()
    calibrator_q.fit(dec_train_full.reshape(-1, 1), y_train)
    probs_test_qsvc = calibrator_q.predict_proba(dec_test_full.reshape(-1, 1))[:, 1]

    # Hybrid Ensembling: Weighted combination of Quantum Kernel Classifier and Calibrated Logistic Baseline
    # This leverages quantum feature mapping in Hilbert space while preserving strong linear calibration
    w_quantum = 0.35
    w_classical = 0.65
    final_probs = w_quantum * probs_test_qsvc + w_classical * probs_test_lr

    # Ensure strictly continuous and valid probabilities [0, 1]
    final_probs = np.clip(final_probs, 0.001, 0.999)

    # 4. Construct Stage 1 Result DataFrame
    result_df = pd.DataFrame({
        ID_COL: test_df[ID_COL].values,
        "predicted_probability": final_probs,
        "prob_classical_lr": probs_test_lr,
        "prob_quantum_qsvc": probs_test_qsvc,
    })

    # Sort descending by predicted probability, tie-breaker: customer_id ascending
    result_df = result_df.sort_values(
        by=["predicted_probability", ID_COL],
        ascending=[False, True]
    ).reset_index(drop=True)

    result_df["rank"] = np.arange(1, len(result_df) + 1)
    result_df["top_10"] = result_df["rank"] <= 10

    # Save required stage1_result.csv and stage1_predictions.csv/json
    submission_s1 = result_df[[ID_COL, "predicted_probability", "rank", "top_10"]].copy()
    submission_s1.to_csv(STAGE1_RESULT_PATH, index=False)
    submission_s1.to_csv(STAGE1_PREDICTIONS_PATH, index=False)
    submission_s1.to_json(STAGE1_PREDICTIONS_JSON, orient="records", indent=2)
    print(f"\n[OK] Successfully generated {STAGE1_RESULT_PATH} and {STAGE1_PREDICTIONS_PATH} with {len(submission_s1)} test customers.")

    top_10_df = result_df[result_df["top_10"]].copy().reset_index(drop=True)
    print("\n--- Top 10 Stage 2 Candidates ---")
    for _, r in top_10_df.iterrows():
        print(f"Rank {int(r['rank']):2d} | {r[ID_COL]} | Prob: {r['predicted_probability']:.4f} (Classical: {r['prob_classical_lr']:.4f}, Quantum: {r['prob_quantum_qsvc']:.4f})")

    return result_df, top_10_df, cv_summary
