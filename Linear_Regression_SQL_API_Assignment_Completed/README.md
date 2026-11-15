# Linear Regression + SQL Ingestion API

This project implements the two assignment requirements:

1. Raw inference data is preprocessed using the SAME fitted preprocessing pipeline used during training.
2. CSV upload is ingested into a SQL database, queried back from SQL, and then passed to `src/utils/data_prep.py` for the train/test split.

## Dataset

The supplied CSV is the Housing dataset with target column `price`.

## Project structure

```text
Linear_Regression_SQL_API_Assignment/
├── main.py
├── requirements.txt
├── README.md
├── data/
│   └── housing.csv
├── models/
│   └── (generated after training)
└── src/
    ├── __init__.py
    ├── inference.py
    ├── sql_ingestion.py
    ├── training.py
    └── utils/
        ├── __init__.py
        └── data_prep.py
```

## Install

```bash
pip install -r requirements.txt
```

## Start server

```bash
uvicorn main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Assignment 2: SQL ingestion + preprocessing

Upload the CSV to:

```text
POST /upload-and-preprocess-data
```

Form-data:

```text
file = housing.csv
```

What happens:

1. CSV is received.
2. CSV is inserted into SQLite SQL database.
3. Data is queried back using SQL.
4. The queried data is passed to `src/utils/data_prep.py`.
5. The target is separated.
6. 80/20 train-test split is performed.
7. The fitted preprocessing pipeline is saved.
8. A Linear Regression model is trained and saved.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/upload-and-preprocess-data"   -F "file=@data/housing.csv"
```

## Assignment 1: Raw inference preprocessing

POST raw/unprocessed data to:

```text
POST /inference
```

JSON example:

```json
{
  "area": 7420,
  "bedrooms": 4,
  "bathrooms": 2,
  "stories": 3,
  "mainroad": "yes",
  "guestroom": "no",
  "basement": "no",
  "hotwaterheating": "no",
  "airconditioning": "yes",
  "parking": 2,
  "prefarea": "yes",
  "furnishingstatus": "furnished"
}
```

The endpoint calls:

```python
return_inference(MODEL_FILE_NAME, inference_data)
```

That method loads the saved fitted preprocessing pipeline and transforms the raw data before calling the Linear Regression model.

The inference data must NOT contain the target `price`.

## Important

`models/model_bundle.pkl` is created after training. Run `/upload-and-preprocess-data` once before `/inference`.
