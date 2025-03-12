import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
import joblib

# Definir la ruta del directorio de trabajo
dir_path = Path(os.getcwd())

# Crear conexión a la base de datos MySQL
engine = create_engine('mysql+pymysql://taller-airflow:mysql@mysql/taller')

# Leer la tabla desde la base de datos
df = pd.read_sql_table('iris_raw', engine)

# PREPROCESAMIENTO

# Quitar duplicados y valores nulos
df_clean = df.drop_duplicates().dropna()

# Seleccionar solo las columnas numéricas para normalizar
num_cols = df_clean.select_dtypes(include=['number']).columns

# Normalización
scaler = StandardScaler()
df_clean[num_cols] = scaler.fit_transform(df_clean[num_cols])

# Guardar el scaler para uso futuro
joblib.dump(scaler, dir_path / "artifacts/scaler.joblib")

# Guardar los datos preprocesados en la base de datos
df_clean.to_sql('iris_cleaned', engine, if_exists='replace', index=False)
print("Datos preprocesados y guardados en 'iris_cleaned'.")
