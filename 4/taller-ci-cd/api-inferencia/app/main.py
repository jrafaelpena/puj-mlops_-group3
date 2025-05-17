import os
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import numpy as np
import pickle
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Literal
import pandas as pd

app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite generar inferencia del dataset de iris"
)

# Métricas Prometheus
REQUEST_COUNT = Counter('predict_requests_total', 'Total de peticiones de predicción')
REQUEST_LATENCY = Histogram('predict_latency_seconds', 'Tiempo de latencia de predicción')

# Modelo global
model = None

@app.post("/load_model/")
def load_model():
    global model
    if model is not None:
        print("✅ Modelo ya cargado")
        return {"message": "Modelo ya cargado"}

    try:
        print("🔄 Cargando modelo desde model.pkl")
        model_path = "model.pkl"
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
        print("✅ Modelo cargado correctamente")
        return {"message": "Modelo cargado correctamente"}
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}")
        raise HTTPException(status_code=500, detail="No se pudo cargar el modelo.")

class PredictionRequest(BaseModel):
    sepal_length: float = Field(..., ge=0.0, le=10.0, example=5.1)
    sepal_width: float = Field(..., ge=0.0, le=10.0, example=3.5)
    petal_length: float = Field(..., ge=0.0, le=10.0, example=1.4)
    petal_width: float = Field(..., ge=0.0, le=10.0, example=0.2)

    class Config:
        schema_extra = {
            "example": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
        }

@app.post("/predict/")
def predict(request: PredictionRequest):
    REQUEST_COUNT.inc()
    global model
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
            
            # Mapeo de clases numéricas a nombres de especies
            species_map = {0: 'setosa', 1: 'versicolor', 2: 'virginica'}
            species_name = species_map.get(prediction[0], 'unknown')

            return {
                "prediction": int(prediction[0]),
                "species": species_name
            }

        except Exception as e:
            print(f"❌ Error en la predicción: {e}")
            raise HTTPException(status_code=500, detail="Error al hacer la predicción.")

@app.get("/")
def read_root():
    return {
        "message": "🌸 API de Modelos de Machine Learning - Grupo 3",
        "description": "Esta API permite realizar inferencias sobre el dataset de iris, clasificando flores en base a sus características.",
        "available_endpoints": {
            "/": "Información general sobre la API",
            "/load_model/": "Carga el modelo desde model.pkl",
            "/predict/": "Realiza una predicción usando el modelo cargado",
            "/metrics": "Expone métricas Prometheus para monitoreo"
        },
        "note": "Asegúrate de llamar primero a /load_model/ antes de usar /predict/."
    }

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)