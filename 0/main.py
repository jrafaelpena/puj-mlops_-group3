from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from joblib import load
import numpy as np

app = FastAPI()

rf_model = load('random_forest_model.joblib')
kmeans_model = load('kmeans_model.joblib')

current_model = "random_forest"

model_options = {"random_forest": rf_model, "kmeans": kmeans_model}

class InputData(BaseModel):
    features: list

@app.get("/")
def read_root():
    return {"message": "API de modelos de Machine Learning"}

@app.post("/predict")
def predict(input_data: InputData):

    if current_model not in model_options:
        raise HTTPException(status_code=400, detail="Modelo no configurado correctamente.")

    model = model_options[current_model]


    if current_model == "random_forest":
        pred = model.predict([input_data.features])
        return {"prediction": int(pred[0])}
    elif current_model == "kmeans":
        cluster = model.predict([input_data.features])
        return {"cluster": int(cluster[0])}

@app.post("/set_model")
def set_model(model_name: str):
    global current_model
    if model_name not in model_options:
        raise HTTPException(status_code=400, detail="Modelo no válido. Use 'random_forest' o 'kmeans'.")
    current_model = model_name
    return {"message": f"Modelo cambiado a {model_name}"}