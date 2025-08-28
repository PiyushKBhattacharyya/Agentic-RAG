from __future__ import annotations
import os
import pandas as pd
from typing import Dict


def load_data(data_dir: str = "data") -> Dict[str, pd.DataFrame]:
    """Load CSV datasets. Assumes three files exist: invoices.csv, pos.csv, receipts.csv."""
    paths = {
        "invoices": os.path.join(data_dir, "invoices.csv"),
        "pos": os.path.join(data_dir, "pos.csv"),
        "receipts": os.path.join(data_dir, "receipts.csv"),
    }
    dfs: Dict[str, pd.DataFrame] = {}
    for name, path in paths.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing data file: {path}")
        df = pd.read_csv(path)
        dfs[name] = df
    return dfs