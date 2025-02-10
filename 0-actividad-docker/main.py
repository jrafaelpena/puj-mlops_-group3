from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from typing import Literal
from pathlib import Path
import joblib
import numpy as np

app = FastAPI(
    title="Machine Learning API - Grupo 3",
    description="Esta API permite predecir el tipo de flor en función de las dimensiones de sus pétalos (dataset iris)."
)

# Carga modelos
dir_path = Path(__file__).parent

log_reg = joblib.load(dir_path / "joblibs/log_reg.joblib")
rf = joblib.load(dir_path / "joblibs/random_forest.joblib")
lgbm = joblib.load(dir_path / "joblibs/lightgbm.joblib")

# Carga la instancia de StandardScaler
scaler = joblib.load(dir_path / "joblibs/scaler.joblib")


models = {
    "log_reg": log_reg,
    "random_forest": rf,
    "lightgbm": lgbm
}


class PredictionRequest(BaseModel):
    features: list[float] = Field(
        ..., min_items=4, max_items=4, 
        description="Lista de 4 variables numéricas: sepal length (4.3 - 7.9), sepal width (2 - 4.4), petal length (1 - 6.9), petal width (0.1 - 2.5).",
        example=[5.4, 1.4, 5.3, 1.4]
    )

class SpecificPredictionRequest(BaseModel):
    model_name: Literal["log_reg", "random_forest", "lightgbm"] = Field(
        ..., description="Puede elegir entre: log_reg, random_forest, lightgbm",
        example="lightgbm"
    )
    features: list[float] = Field(
        ..., min_items=4, max_items=4, 
        description="Lista de 4 variables numéricas: sepal length (4.3 - 7.9), sepal width (2 - 4.4), petal length (1 - 6.9), petal width (0.1 - 2.5).",
        example=[5.4, 1.4, 5.3, 1.4]
    )

@app.get("/")
def read_root():
    return {"message": "API de modelos de Machine Learning - Grupo 3!"}

@app.post("/predict/")
def predict(request: PredictionRequest):
    model = models["log_reg"]
    X_input = np.array(request.features).reshape(1, -1)

    X_input = scaler.transform(X_input)

    prediction = model.predict(X_input).tolist()
    return {"model": "log_reg", "prediction": prediction}

@app.post("/predict_specific_model/")
def predict_specific_model(request: SpecificPredictionRequest):
    model = models[request.model_name]
    X_input = np.array(request.features).reshape(1, -1)

    X_input = scaler.transform(X_input)

    prediction = model.predict(X_input).tolist()
    return {"model": request.model_name, "prediction": prediction}

