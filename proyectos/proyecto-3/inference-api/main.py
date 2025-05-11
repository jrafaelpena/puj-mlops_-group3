import os
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import numpy as np
import mlflow.pyfunc
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Literal
import pandas as pd
from sqlalchemy import create_engine
from mlflow import MlflowClient

app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite generar inferencia del dataset de diabetes"
)

# Métricas Prometheus
REQUEST_COUNT = Counter('predict_requests_total', 'Total de peticiones de predicción')
REQUEST_LATENCY = Histogram('predict_latency_seconds', 'Tiempo de latencia de predicción')

# Configuración de MLflow
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
MLFLOW_MODEL_URI = "models:/diabetes@champion"

# Parámetros para conexión PostgreSQL
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'train_data')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'project3')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'project3')

# SQLAlchemy connection string for PostgreSQL
CONNECTION_STRING = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Modelo global
model = None
model_version = None  # Nuevo


@app.post("/load_model/")
def load_model():
    global model, model_version
    if model is not None and model_version is not None:
        print(f"✅ Modelo ya cargado (alias: 'champion', versión: {model_version})")
        return {"message": f"Modelo ya cargado (alias: 'champion', versión: {model_version})"}

    try:
        print(f"🔄 Cargando modelo desde MLflow: {MLFLOW_MODEL_URI}")
        model = mlflow.pyfunc.load_model(MLFLOW_MODEL_URI)
        client = MlflowClient()
        version_info = client.get_model_version_by_alias("diabetes", "champion")
        model_version = version_info.version  # Almacenar versión
        print(f"✅ Modelo cargado correctamente (alias: 'champion', versión: {model_version})")
        return {"message": f"Modelo cargado correctamente (alias: 'champion', versión: {model_version})"}
    except mlflow.exceptions.MlflowException as e:
        print(f"❌ Error al cargar el modelo: {e}")
        raise HTTPException(status_code=500, detail="No se pudo cargar el modelo.")
    
class PredictionRequest(BaseModel):
    race: Literal['Caucasian', 'AfricanAmerican', '?', 'Other', 'Asian']
    gender: Literal['Female', 'Male', 'Unknown/Invalid']
    age: Literal['[0-10)', '[10-20)', '[20-30)', '[30-40)', '[40-50)', 
                 '[50-60)', '[60-70)', '[70-80)', '[80-90)', '[90-100)']
    time_in_hospital: int = Field(..., ge=1, le=14)
    payer_code: Literal[
        '?', 'MC', 'MD', 'HM', 'UN', 'BC', 'SP', 'CP', 'SI', 'DM', 'CM',
        'CH', 'PO', 'WC', 'OT', 'OG', 'MP', 'FR'
    ]
    num_lab_procedures: int = Field(..., ge=1, le=132)
    num_procedures: int = Field(..., ge=0, le=6)
    num_medications: int = Field(..., ge=1, le=81)
    number_outpatient: int = Field(..., ge=0, le=42)
    number_emergency: int = Field(..., ge=0, le=76)
    number_inpatient: int = Field(..., ge=0, le=21)
    number_diagnoses: int = Field(..., ge=1, le=16)
    metformin: Literal['No', 'Steady', 'Up', 'Down']
    glipizide: Literal['No', 'Steady', 'Up', 'Down']
    glyburide: Literal['No', 'Steady', 'Up', 'Down']
    insulin: Literal['No', 'Up', 'Steady', 'Down']
    change: Literal['No', 'Ch']
    diabetesmed: Literal['No', 'Yes']

    class Config:
        schema_extra = {
            "example": {
                "race": "Caucasian",
                "gender": "Female",
                "age": "[70-80)",
                "time_in_hospital": 5,
                "payer_code": "MC",
                "num_lab_procedures": 45,
                "num_procedures": 1,
                "num_medications": 18,
                "number_outpatient": 0,
                "number_emergency": 0,
                "number_inpatient": 1,
                "number_diagnoses": 8,
                "metformin": "No",
                "glipizide": "Steady",
                "glyburide": "No",
                "insulin": "Up",
                "change": "Ch",
                "diabetesmed": "Yes"
            }
        }

@app.post("/predict/")
def predict(request: PredictionRequest):
    REQUEST_COUNT.inc()
    global model, model_version
    if model is None:
        return {
            "error": "Modelo no cargado todavía.",
            "message": "Por favor use el endpoint /load_model/ para cargar el modelo antes de hacer predicciones."
        }

    with REQUEST_LATENCY.time():
        try:
            input_dict = request.dict()
            input_df = pd.DataFrame([input_dict])

            # Realiza predicción
            prediction = model.predict(input_df)

            # Preparar para registrar en DB
            input_df['readmitted'] = prediction
            input_df['dataset'] = 'Inference'

            try:
                engine = create_engine(CONNECTION_STRING)
                input_df.to_sql("clean_data", con=engine, if_exists="append", index=False)
                engine.dispose()
            except Exception as db_err:
                print(f"⚠️ Error al guardar en la base de datos: {db_err}")

            return {
                "prediction": prediction[0],
                "model_alias": "champion",
                "model_version": model_version
            }

        except Exception as e:
            print(f"❌ Error en la predicción: {e}")
            raise HTTPException(status_code=500, detail="Error al hacer la predicción.")

@app.get("/")
def read_root():
    return {
        "message": "🌲 API de Modelos de Machine Learning - Grupo 3",
        "description": "Esta API permite realizar inferencias sobre el dataset de diabetes, utilizando modelos registrados en MLflow.",
        "available_endpoints": {
            "/": "Información general sobre la API",
            "/load_model/": "Carga el modelo registrado como 'champion' en MLflow",
            "/predict/": "Realiza una predicción usando el modelo cargado",
            "/metrics": "Expone métricas Prometheus para monitoreo"
        },
        "note": "Asegúrate de llamar primero a /load_model/ antes de usar /predict/."
    }

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)