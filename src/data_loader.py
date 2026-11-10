"""
Data Loader for the Vortex Pipeline
Handles extraction, validation, and traceability of customer IDs across sheets.
"""

import pandas as pd
from typing import Tuple, Dict, Any
from .config import DATA_PATH, ID_COL, TARGET_COL


def load_dataset() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Loads and validates all sheets from the hackathon release workbook.
    
    Returns:
        train_df: DataFrame of 300 labeled training customers
        test_df: DataFrame of 100 test customers with customer_ids
        stage2_df: DataFrame of 400 customer operational parameters
        constraints: Dictionary of Stage 2 operational constraints
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")

    # Load sheets
    excel_file = pd.ExcelFile(DATA_PATH)
    train_df = pd.read_excel(excel_file, sheet_name="Stage1_Train")
    test_df = pd.read_excel(excel_file, sheet_name="Stage1_Test")
    stage2_df = pd.read_excel(excel_file, sheet_name="Stage2_Data")
    constraints_df = pd.read_excel(excel_file, sheet_name="Stage2_Constraints")

    # Validate shapes
    assert len(train_df) == 300, f"Expected 300 training records, got {len(train_df)}"
    assert len(test_df) == 100, f"Expected 100 test records, got {len(test_df)}"
    assert len(stage2_df) == 400, f"Expected 400 Stage2 operational records, got {len(stage2_df)}"

    train_ids = set(train_df[ID_COL])
    remaining_ids = set(stage2_df[ID_COL]) - train_ids
    assert len(remaining_ids) == 100, f"Expected exactly 100 remaining IDs, got {len(remaining_ids)}"

    if ID_COL not in test_df.columns:
        # Fallback assignment if customer_id was omitted
        sorted_remaining = [cid for cid in stage2_df[ID_COL] if cid not in train_ids]
        test_df[ID_COL] = sorted_remaining
    else:
        # Validate that the official test customer IDs match the expected remaining Stage2 IDs
        assert set(test_df[ID_COL]) == remaining_ids, "Test customer IDs do not match remaining Stage2 IDs"
        assert len(test_df[ID_COL].unique()) == 100, "Duplicate customer IDs found in test set"

    # Extract constraints into a convenient dictionary
    constraints = {}
    for _, row in constraints_df.iterrows():
        param = str(row["parameter"]).strip()
        val = row["value"]
        constraints[param] = val

    return train_df, test_df, stage2_df, constraints
