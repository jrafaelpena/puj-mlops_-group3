from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np
import mlflow.pyfunc
import os
from threading import Lock

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

# Modelo y lock global
model = None
model_lock = Lock()

@app.on_event("startup")
def startup_event():
    global model
    with model_lock:
        if model is None:
            try:
                print(f"🔄 Cargando modelo desde MLflow: {MLFLOW_MODEL_URI}")
                model = mlflow.pyfunc.load_model(MLFLOW_MODEL_URI)
                print(f"✅ Modelo cargado correctamente.")
            except mlflow.exceptions.MlflowException as e:
                print(f"❌ Error al cargar el modelo en el inicio: {e}")
                raise RuntimeError(f"No se pudo cargar el modelo durante el startup.")

class PredictionRequest(BaseModel):
    features: list[float] = Field(
        ..., min_items=10, max_items=10,
        description="Lista de 10 variables numéricas: Elevation, Aspect, Slope, Horizontal_Distance_To_Hydrology, Vertical_Distance_To_Hydrology, Horizontal_Distance_To_Roadways, Hillshade_9am, Hillshade_Noon, Hillshade_3pm, Horizontal_Distance_To_Fire_Points.",
        example=[3000, 45, 10, 100, 50, 200, 220, 230, 180, 300]
    )

@app.post("/predict/")
def predict(request: PredictionRequest):
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible. Intente más tarde.")
    
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
