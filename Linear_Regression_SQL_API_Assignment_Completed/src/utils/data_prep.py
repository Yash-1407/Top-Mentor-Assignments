"""Data preparation utilities used by the SQL-ingestion training flow."""

from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split


def split_data(
    df: pd.DataFrame,
    target_column: str = "price",
    test_size: float = 0.20,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Separate target and perform the standard 80/20 train-test split."""
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' was not found.")

    X = df.drop(columns=[target_column])
    y = df[target_column]

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )
