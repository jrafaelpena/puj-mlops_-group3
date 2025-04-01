from fastapi import FastAPI, HTTPException
from typing import Optional
import random
import json
import time
import csv
import os

MIN_UPDATE_TIME = 120  # Aca pueden cambiar el tiempo minimo para cambiar bloque de información

app = FastAPI()

# Cargar los datos del archivo CSV
data = []
with open('/data/covertype.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    next(reader, None)
    for row in reader:
        data.append(row)

# Definir la función para generar la fracción de datos aleatoria
def get_batch_data(batch_number: int, batch_size: int):
    start_index = batch_number * batch_size
    end_index = start_index + batch_size
    
    # Ajustar si el rango supera el tamaño de los datos
    if end_index > len(data):
        end_index = len(data)
    
    # Obtener datos aleatorios dentro del rango del grupo
    random_data = random.sample(data[start_index:end_index], min(batch_size // 10, len(data[start_index:end_index])))
    return random_data

# Cargar información previa si existe
if os.path.isfile('/data/timestamps.json'):
    with open('/data/timestamps.json', "r") as f:
        timestamps = json.load(f)
else:
    # Inicializar el diccionario para almacenar los timestamps de cada grupo
    timestamps = {str(group_number): [0, -1] for group_number in range(1, 11)}  # el valor está definido como [timestamp, batch]

# Definir la ruta de la API
@app.get("/")
async def root():
    return {"Proyecto 2": "Extracción de datos, entrenamiento de modelos."}

@app.get("/data")
async def read_data(group_number: int):
    global timestamps

    # Verificar si el número de grupo es válido
    if group_number < 1 or group_number > 10:
        raise HTTPException(status_code=400, detail="Número de grupo inválido")
    
    # Verificar si el número de conteo es adecuado
    if timestamps[str(group_number)][1] >= 9:  # Ajustado para que sean 10 batches (0-9)
        raise HTTPException(status_code=400, detail="Ya se recolectó toda la información minima necesaria")
    
    current_time = time.time()
    last_update_time = timestamps[str(group_number)][0]
    
    # Verificar si han pasado más de MIN_UPDATE_TIME segundos desde la última actualización
    if current_time - last_update_time > MIN_UPDATE_TIME:
        # Actualizar el timestamp y obtener nuevos datos
        timestamps[str(group_number)][0] = current_time
        timestamps[str(group_number)][1] += 1  # Incrementar en 1 por cada nuevo batch
    
    # Calcular el tamaño del lote dinámicamente
    batch_size = len(data) // 10
    random_data = get_batch_data(timestamps[str(group_number)][1], batch_size)  # Usamos el número de batch actual
    
    # Guardar los timestamps actualizados
    with open('/data/timestamps.json', 'w') as file:
        file.write(json.dumps(timestamps))
    
    return {"group_number": group_number, "batch_number": timestamps[str(group_number)][1], "data": random_data}

@app.get("/restart_data_generation")
async def restart_data(group_number: int):
    # Verificar si el número de grupo es válido
    if group_number < 1 or group_number > 10:
        raise HTTPException(status_code=400, detail="Número de grupo inválido")

    # Reiniciar el proceso para el grupo seleccionado
    timestamps[str(group_number)][0] = 0
    timestamps[str(group_number)][1] = -1  # Reiniciar el batch
    with open('/data/timestamps.json', 'w') as file:
        file.write(json.dumps(timestamps))
    return {'ok'}