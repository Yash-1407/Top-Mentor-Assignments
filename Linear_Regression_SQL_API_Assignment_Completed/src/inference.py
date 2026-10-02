"""Raw-data inference implementation."""

from pathlib import Path
from typing import Any
import joblib
import pandas as pd


def _to_dataframe(inference_data: Any) -> pd.DataFrame:
    """Convert common API payload shapes to a DataFrame."""
    if isinstance(inference_data, pd.DataFrame):
        return inference_data.copy()

    if isinstance(inference_data, dict):
        # Supports both one record and {"records": [...]}.
        if "records" in inference_data and isinstance(
            inference_data["records"], list
        ):
            return pd.DataFrame(inference_data["records"])
        return pd.DataFrame([inference_data])

    if isinstance(inference_data, list):
        return pd.DataFrame(inference_data)

    raise TypeError(
        "inference_data must be a pandas DataFrame, dictionary, or list."
    )


def return_inference(
    MODEL_FILE_NAME: str | Path,
    inference_data: Any,
):
    """Perform inference on RAW data.

    The saved sklearn Pipeline contains the fitted imputer, scaler and
    one-hot encoder. Calling model.predict(raw_df) automatically performs
    the exact same preprocessing learned during training.
    """
    bundle = joblib.load(MODEL_FILE_NAME)

    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    raw_df = _to_dataframe(inference_data)

    missing_columns = [
        col for col in feature_columns if col not in raw_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing inference columns: {missing_columns}"
        )

    # Ignore an accidentally supplied target column.
    raw_features = raw_df[feature_columns].copy()

    # IMPORTANT: Do not manually fit/transform here.
    # model.predict() invokes the already-fitted training preprocessor.
    predictions = model.predict(raw_features)

    result = raw_df.copy()
    result["prediction"] = predictions

    return result


def return_inference_from_excel(
    MODEL_FILE_NAME: str | Path,
    excel_path: str,
):
    raw_data = pd.read_excel(excel_path)
    return return_inference(MODEL_FILE_NAME, raw_data)
