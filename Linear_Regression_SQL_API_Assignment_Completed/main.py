from pathlib import Path
import os
import tempfile

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Any

from src.sql_ingestion import ingest_csv_to_sql, query_data_from_sql
from src.training import train_linear_regression, MODEL_FILE_NAME
from src.inference import return_inference


app = FastAPI(
    title="Linear Regression SQL Ingestion API",
    version="1.0.0",
)


class InferenceRequest(BaseModel):
    data: Any


@app.get("/")
def root():
    return {
        "message": "Linear Regression API is running",
        "training_endpoint": "/upload-and-preprocess-data",
        "inference_endpoint": "/inference",
    }


@app.post("/upload-and-preprocess-data")
async def upload_and_preprocess_data(
    file: UploadFile = File(...),
):
    """Assignment 2.

    CSV -> SQL database -> SQL query -> data_prep split -> training.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are accepted.",
        )

    temp_path = None

    try:
        suffix = ".csv"
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        # 1. Ingest uploaded CSV into SQL.
        rows_inserted = ingest_csv_to_sql(temp_path)

        # 2. Query the data back from SQL.
        sql_df = query_data_from_sql("housing")

        # 3 & 4. The training function calls src/utils/data_prep.py,
        # performs the train/test split, fits preprocessing and trains
        # Linear Regression.
        metrics = train_linear_regression(
            sql_df,
            target_column="price",
        )

        return {
            "message": "CSV ingested into SQL, queried, split and model trained successfully.",
            "filename": file.filename,
            "sql_table": "housing",
            "rows_ingested": rows_inserted,
            "rows_queried": len(sql_df),
            "target_column": "price",
            "split": "80% train / 20% test",
            "model_file": str(MODEL_FILE_NAME),
            "metrics": metrics,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/inference")
def inference(request: InferenceRequest):
    """Assignment 1: accept RAW inference data and preprocess it."""
    if not Path(MODEL_FILE_NAME).exists():
        raise HTTPException(
            status_code=400,
            detail=(
                "Model not found. First upload the training CSV to "
                "/upload-and-preprocess-data."
            ),
        )

    try:
        result = return_inference(
            MODEL_FILE_NAME,
            request.data,
        )

        return {
            "message": "Raw inference data was preprocessed using the training pipeline and prediction was completed.",
            "predictions": result.to_dict(orient="records"),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
