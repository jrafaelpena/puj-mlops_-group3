import os
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import numpy as np
import mlflow.pyfunc
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional
import pandas as pd
from mlflow import MlflowClient

app = FastAPI(
    title="House Prices Prediction API - Grupo 3",
    description="Esta API permite generar inferencia del dataset de precios de casas"
)

# Métricas Prometheus
REQUEST_COUNT = Counter('predict_requests_total', 'Total de peticiones de predicción')
REQUEST_LATENCY = Histogram('predict_latency_seconds', 'Tiempo de latencia de predicción')

# Configuración de MLflow
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
MLFLOW_MODEL_URI = "models:/house_prices@champion"

# Modelo global
model = None
model_version = None


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
        version_info = client.get_model_version_by_alias("house_prices", "champion")
        model_version = version_info.version
        print(f"✅ Modelo cargado correctamente (alias: 'champion', versión: {model_version})")
        return {"message": f"Modelo cargado correctamente (alias: 'champion', versión: {model_version})"}
    except mlflow.exceptions.MlflowException as e:
        print(f"❌ Error al cargar el modelo: {e}")
        raise HTTPException(status_code=500, detail="No se pudo cargar el modelo.")


class HousePredictionRequest(BaseModel):
    bed: int = Field(..., ge=1, le=190, description="Número de habitaciones")
    bath: int = Field(..., ge=1, le=163, description="Número de baños")
    acre_lot: float = Field(..., ge=0.0, le=100000.0, description="Tamaño del lote en acres")
    city: str = Field(..., min_length=1, max_length=100, description="Ciudad")
    state: str = Field(..., min_length=1, max_length=50, description="Estado")
    zip_code: int = Field(..., ge=1000, le=99999, description="Código postal")
    house_size: int = Field(..., ge=1500, le=1560780, description="Tamaño de la casa en pies cuadrados")

    class Config:
        schema_extra = {
            "example": {
                "bed": 3,
                "bath": 2,
                "acre_lot": 0.23,
                "city": "Pleasantville",
                "state": "New Jersey",
                "zip_code": 8232,
                "house_size": 1656
            }
        }


@app.post("/predict/")
def predict(request: HousePredictionRequest):
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

            return {
                "predicted_price": float(prediction[0]),
                "model_alias": "champion",
                "model_version": model_version,
                "input_features": input_dict
            }

        except Exception as e:
            print(f"❌ Error en la predicción: {e}")
            raise HTTPException(status_code=500, detail="Error al hacer la predicción.")


@app.get("/")
def read_root():
    return {
        "message": "🏠 API de Predicción de Precios de Casas - Grupo 3",
        "description": "Esta API permite realizar predicciones de precios de casas utilizando modelos registrados en MLflow.",
        "available_endpoints": {
            "/": "Información general sobre la API",
            "/load_model/": "Carga el modelo registrado como 'champion' en MLflow",
            "/predict/": "Realiza una predicción de precio usando el modelo cargado",
            "/metrics": "Expone métricas Prometheus para monitoreo"
        },
        "note": "Asegúrate de llamar primero a /load_model/ antes de usar /predict/.",
        "features": {
            "bed": "Número de habitaciones (1-190)",
            "bath": "Número de baños (1-163)",
            "acre_lot": "Tamaño del lote en acres (0.0-100000.0)",
            "city": "Ciudad",
            "state": "Estado",
            "zip_code": "Código postal (1000-99999)",
            "house_size": "Tamaño de la casa en pies cuadrados (1500-1560780)"
        }
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)