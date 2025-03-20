from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np
import mlflow.pyfunc
import os
import mlflow

app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite predecir el tipo de flor en función de las dimensiones de sus pétalos (dataset iris)."
)

# Configuración de MLflow
MLFLOW_TRACKING_URI = "http://10.43.101.189:5000"
os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://10.43.101.189:9000"
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MLFLOW_MODEL_URI = "models:/iris_model@champion"
model = None

def load_model():
    """Carga el modelo desde MLflow si no está disponible"""
    global model
    print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
    if model is None:
        try:
            model = mlflow.pyfunc.load_model(MLFLOW_MODEL_URI)
            print(f"Modelo cargado correctamente desde MLflow: {MLFLOW_MODEL_URI}")
        except mlflow.exceptions.MlflowException as e:
            print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
            print(f"Error de MLflow al cargar el modelo: {e}")
            raise HTTPException(status_code=500, detail=f"Error en MLflow al cargar el modelo.")


class PredictionRequest(BaseModel):
    features: list[float] = Field(
        ..., min_items=4, max_items=4,
        description="Lista de 4 variables numéricas: sepal length, sepal width, petal length, petal width.",
        example=[5.4, 1.4, 5.3, 1.4]
    )

@app.post("/predict/")
def predict(request: PredictionRequest):
    load_model()  # Carga el modelo si no está disponible

    X_input = np.array(request.features).reshape(1, -1)
    try:
        prediction = model.predict(X_input).tolist()
        return {"model": "MLflow Model", "prediction": prediction}
    except Exception as e:
        print(f"❌ Error en la predicción: {e}")
        raise HTTPException(status_code=500, detail="Error al hacer la predicción.")

@app.get("/")
def read_root():
    return {
        "message": "API de modelos de Machine Learning - Grupo 3!",
        "endpoints": {
            "/predict/": "Realiza una predicción usando el modelo almacenado en MLflow"
        }
    }