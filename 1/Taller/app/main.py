from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from typing import Literal
from pathlib import Path
import joblib
import numpy as np
import os

app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite predecir el tipo de flor en función de las dimensiones de sus pétalos (dataset iris)."
)

dir_path = Path(os.getcwd()) / "artifacts"
models = {}

def load_models():
    """Carga modelos dinámicamente desde /artifacts/"""
    global models
    models.clear()
    
    for model_file in dir_path.glob("*.joblib"):
        model_name = model_file.stem
        try:
            models[model_name] = joblib.load(model_file)
        except Exception as e:
            print(f"Error al cargar {model_file.name}: {e}")

@app.get("/")
def read_root():
    return {
        "message": "API de modelos de Machine Learning - Grupo 3!",
        "endpoints": {
            "/predict/": "Realiza una predicción con el modelo por defecto (log_reg)",
            "/predict_specific_model/": "Realiza una predicción con un modelo específico",
            "/available_models/": "Lista los modelos disponibles",
            "/reload_models/": "Recarga los modelos sin reiniciar el servidor"
        }
    }

# Carga los modelos al iniciar
@app.on_event("startup")
def startup_event():
    load_models()

@app.get("/reload_models/")
def reload_models():
    """Recarga los modelos en tiempo real sin reiniciar el servidor"""
    load_models()
    return {"message": "Modelos recargados", "available_models": list(models.keys())}

@app.get("/available_models/")
def available_models():
    """Lista los modelos disponibles"""
    return {
        "available_models": [
            {"key": name, "file_name": f"{name}.joblib", "type": str(type(model))}
            for name, model in models.items()
        ]
    }

class PredictionRequest(BaseModel):
    features: list[float] = Field(
        ..., min_items=4, max_items=4, 
        description="Lista de 4 variables numéricas: sepal length (4.3 - 7.9), sepal width (2 - 4.4), petal length (1 - 6.9), petal width (0.1 - 2.5).",
        example=[5.4, 1.4, 5.3, 1.4]
    )

@app.post("/predict/")
def predict(request: PredictionRequest):
    if "log_reg" not in models:
        raise HTTPException(status_code=404, detail="Modelo log_reg no encontrado. Recargue los modelos.")
    
    scaler = models.get("scaler")
    if not scaler:
        raise HTTPException(status_code=500, detail="Scaler no encontrado. Recargue los modelos.")

    model = models["log_reg"]
    X_input = np.array(request.features).reshape(1, -1)
    X_input = scaler.transform(X_input)
    prediction = model.predict(X_input).tolist()
    
    return {"model": "log_reg", "prediction": prediction}

class SpecificPredictionRequest(BaseModel):
    model_name: str = Field(..., description="Nombre del modelo disponible en /available_models/")
    features: list[float] = Field(
        ..., min_items=4, max_items=4, 
        description="Lista de 4 variables numéricas: sepal length (4.3 - 7.9), sepal width (2 - 4.4), petal length (1 - 6.9), petal width (0.1 - 2.5).",
        example=[5.4, 1.4, 5.3, 1.4]
    )

@app.post("/predict_specific_model/")
def predict_specific_model(request: SpecificPredictionRequest):
    if request.model_name not in models:
        raise HTTPException(status_code=404, detail=f"Modelo '{request.model_name}' no encontrado. Verifique /available_models/")
    
    scaler = models.get("scaler")
    if not scaler:
        raise HTTPException(status_code=500, detail="Scaler no encontrado. Recargue los modelos.")

    model = models[request.model_name]
    X_input = np.array(request.features).reshape(1, -1)
    X_input = scaler.transform(X_input)
    prediction = model.predict(X_input).tolist()
    
    return {"model": request.model_name, "prediction": prediction}
