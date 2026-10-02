from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import joblib
import os
import tempfile
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error

app = FastAPI(title="ML Training and Inference API")
MODEL_PATH = "model.pkl"

@app.get("/")
def home():
    return {
        "message": "ML Training and Inference API is running.",
        "endpoints": ["/train", "/predict"]
    }

@app.post("/train")
async def train_model(
    file: UploadFile = File(...),
    target_column: str = Form(...),
    problem_type: str = Form(...)
):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed.")

    problem_type = problem_type.lower()
    if problem_type not in ("classification", "regression"):
        raise HTTPException(
            status_code=400,
            detail="problem_type must be classification or regression."
        )

    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        df = pd.read_excel(temp_file_path)

        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded Excel file is empty.")
        if target_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Target column '{target_column}' not found."
            )

        df = df.dropna(subset=[target_column])
        X = df.drop(columns=[target_column])
        y = df[target_column]

        numeric_features = X.select_dtypes(
            include=["int64", "float64", "int32", "float32"]
        ).columns.tolist()
        categorical_features = X.select_dtypes(
            include=["object", "category", "bool"]
        ).columns.tolist()

        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])

        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore"))
        ])

        preprocessing = ColumnTransformer([
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features)
        ])

        if problem_type == "classification":
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)

        pipeline = Pipeline([
            ("preprocessing", preprocessing),
            ("model", model)
        ])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        if problem_type == "classification":
            metric_name = "accuracy"
            score = accuracy_score(y_test, predictions)
        else:
            metric_name = "rmse"
            score = mean_squared_error(y_test, predictions) ** 0.5

        joblib.dump({
            "pipeline": pipeline,
            "target_column": target_column,
            "problem_type": problem_type,
            "feature_columns": X.columns.tolist()
        }, MODEL_PATH)

        return {
            "message": "Model trained successfully.",
            "filename": file.filename,
            "rows": len(df),
            "features": X.columns.tolist(),
            "target_column": target_column,
            "problem_type": problem_type,
            metric_name: float(score)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=400,
            detail="No trained model found. Train the model first."
        )

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed.")

    temp_file_path = None
    try:
        model_data = joblib.load(MODEL_PATH)
        pipeline = model_data["pipeline"]
        feature_columns = model_data["feature_columns"]

        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        df = pd.read_excel(temp_file_path)

        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded Excel file is empty.")

        missing_columns = [
            column for column in feature_columns if column not in df.columns
        ]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Missing required feature columns.",
                    "missing_columns": missing_columns
                }
            )

        X = df[feature_columns]
        predictions = pipeline.predict(X)

        result = df.copy()
        result["prediction"] = predictions
        result = result.replace({np.nan: None})

        return {
            "message": "Inference completed successfully.",
            "rows": len(result),
            "predictions": result.to_dict(orient="records")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
