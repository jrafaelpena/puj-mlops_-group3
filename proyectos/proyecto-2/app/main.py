from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np
import mlflow.pyfunc
import os
import mlflow

app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite predecir el tipo de cobertura forestal en función de características numéricas (Forest Cover Dataset)."
)

# Configuración de MLflow
MLFLOW_TRACKING_URI = "http://mlflow:5000"
os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://minio:9000"
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MLFLOW_MODEL_URI = "models:/forest_cover@champion"
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
        ..., min_items=10, max_items=10,
        description="Lista de 10 variables numéricas: Elevation, Aspect, Slope, Horizontal_Distance_To_Hydrology, Vertical_Distance_To_Hydrology, Horizontal_Distance_To_Roadways, Hillshade_9am, Hillshade_Noon, Hillshade_3pm, Horizontal_Distance_To_Fire_Points.",
        example=[3000, 45, 10, 100, 50, 200, 220, 230, 180, 300]
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
            "/predict/": "Realiza una predicción del tipo de cobertura forestal usando el modelo almacenado en MLflow"
        }
    }