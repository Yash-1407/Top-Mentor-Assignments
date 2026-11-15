# ML Training and Inference API

## Assignment 1: Training Endpoint
POST `/train`

Form-data:
- `file`: Excel file (.xlsx/.xls)
- `target_column`: target column name
- `problem_type`: `classification` or `regression`

## Assignment 2: Inference Endpoint
POST `/predict`

Form-data:
- `file`: Excel file containing the feature columns used during training.

## Run
```bash
pip install -r requirements.txt
python main.py
```

Swagger UI:
http://127.0.0.1:8000/docs

`model.pkl` is generated automatically after successful training.
