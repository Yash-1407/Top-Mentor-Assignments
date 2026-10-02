"""Linear Regression training pipeline."""

from pathlib import Path
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.utils.data_prep import split_data

MODEL_FILE_NAME = Path("models/model_bundle.pkl")


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric_features = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_features = X.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )


def train_linear_regression(
    df: pd.DataFrame,
    target_column: str = "price",
):
    X_train, X_test, y_train, y_test = split_data(
        df,
        target_column=target_column,
        test_size=0.20,
        random_state=42,
    )

    preprocessor = build_preprocessor(X_train)

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", LinearRegression()),
        ]
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    rmse = mean_squared_error(y_test, predictions) ** 0.5
    metrics = {
        "mae": float(mean_absolute_error(y_test, predictions)),
        "rmse": float(rmse),
        "r2": float(r2_score(y_test, predictions)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
    }

    MODEL_FILE_NAME.parent.mkdir(parents=True, exist_ok=True)

    # The fitted preprocessing pipeline is stored inside the model Pipeline.
    # Therefore inference can receive RAW data and transform it identically.
    bundle = {
        "model": model,
        "target_column": target_column,
        "feature_columns": X_train.columns.tolist(),
        "metrics": metrics,
    }

    joblib.dump(bundle, MODEL_FILE_NAME)

    return metrics
