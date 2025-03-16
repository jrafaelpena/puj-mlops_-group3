from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
import joblib
import numpy as np

app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite predecir el tipo de flor en función de las dimensiones de sus pétalos (dataset iris)."
)

MODEL_PATH = Path("artifacts/iris_model.joblib")
model = None

def load_model():
    """Carga el modelo si está disponible"""
    global model
    if model is None or not MODEL_PATH.exists():
        if MODEL_PATH.exists():
            try:
                model = joblib.load(MODEL_PATH)
                print(f"Modelo cargado correctamente desde {MODEL_PATH}")
            except Exception as e:
                print(f"Error al cargar el modelo: {e}")
                raise HTTPException(status_code=500, detail="Error al cargar el modelo.")
        else:
            raise HTTPException(status_code=404, detail="Modelo no encontrado. Entrene y cargue el modelo en 'artifacts/iris_model.joblib'.")

class PredictionRequest(BaseModel):
    features: list[float] = Field(
        ..., min_items=4, max_items=4,
        description="Lista de 4 variables numéricas: sepal length, sepal width, petal length, petal width.",
        example=[5.4, 1.4, 5.3, 1.4]
    )

@app.post("/predict/")
def predict(request: PredictionRequest):
    load_model()  # Se carga el modelo en cada petición si no está disponible
    
    X_input = np.array(request.features).reshape(1, -1)
    prediction = model.predict(X_input).tolist()
    
    return {"model": "RandomForestClassifier", "prediction": prediction}

@app.get("/")
def read_root():
    return {
        "message": "API de modelos de Machine Learning - Grupo 3!",
        "endpoints": {
            "/predict/": "Realiza una predicción usando el modelo RandomForestClassifier"
        }
    }