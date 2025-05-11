import os
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import numpy as np
import mlflow.pyfunc
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Literal
import time
import random


app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite generar inferencia del dataset de diabetes"
)

# Métricas Prometheus
REQUEST_COUNT = Counter('predict_requests_total', 'Total de peticiones de predicción')
REQUEST_LATENCY = Histogram('predict_latency_seconds', 'Tiempo de latencia de predicción')

# Configuración de MLflow
MLFLOW_TRACKING_URI = "http://mlflow:5000"
os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://minio:9000"
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
MLFLOW_MODEL_URI = "models:/forest_cover@champion"

# Modelo global
model = None

@app.post("/load_model/")
def load_model():
    global model
    if model is not None:
        # Extract model version from URI
        version_info = mlflow.get_model_version_by_alias("forest_cover", "champion")
        version = version_info.version
        print(f"✅ Modelo ya cargado (alias: 'champion', versión: {version})")
        return {"message": f"Modelo ya cargado (alias: 'champion', versión: {version})"}

    try:
        print(f"🔄 Cargando modelo desde MLflow: {MLFLOW_MODEL_URI}")
        model = mlflow.pyfunc.load_model(MLFLOW_MODEL_URI)
        version_info = mlflow.get_model_version_by_alias("forest_cover", "champion")
        version = version_info.version
        print(f"✅ Modelo cargado correctamente (alias: 'champion', versión: {version})")
        return {"message": f"Modelo cargado correctamente (alias: 'champion', versión: {version})"}
    except mlflow.exceptions.MlflowException as e:
        print(f"❌ Error al cargar el modelo: {e}")
        raise HTTPException(status_code=500, detail="No se pudo cargar el modelo.")
    
class PredictionRequest(BaseModel):
    features: list[float] = Field(
        ..., min_items=10, max_items=10,
        description="Lista de 10 variables numéricas: Elevation, Aspect, Slope, Horizontal_Distance_To_Hydrology, Vertical_Distance_To_Hydrology, Horizontal_Distance_To_Roadways, Hillshade_9am, Hillshade_Noon, Hillshade_3pm, Horizontal_Distance_To_Fire_Points.",
        example=[3000, 45, 10, 100, 50, 200, 220, 230, 180, 300]
    )

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
    global model
    if model is None:
        return {
            "error": "Modelo no cargado todavía.",
            "message": "Por favor use el endpoint /load_model/ para cargar el modelo antes de hacer predicciones."
        }
    


    X_input = np.array(request.features).reshape(1, -1)
    try:
        pass
    except Exception as e:
        print(f"❌ Error en la predicción: {e}")
        raise HTTPException(status_code=500, detail="Error al hacer la predicción.")