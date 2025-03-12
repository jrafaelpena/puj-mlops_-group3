from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
import joblib

@dag(
    dag_id="3-clean-data-train-model",
    start_date=days_ago(1),
    schedule_interval="@once",
    catchup=False
)
def clean_train_and_upload_iris_data():
    
    @task
    def clean_data():
        engine = create_engine('mysql+pymysql://taller-airflow:mysql@mysql/taller')
        
        # Leemos los datos preprocesados
        df = pd.read_sql_table('iris_raw', engine)
        
        # Eliminamos duplicados y filas con NaN
        df_clean = df.drop_duplicates().dropna()
        
        # Convertimos la columna species a valores numéricos
        species_mapping = {species: idx for idx, species in enumerate(sorted(df_clean['species'].unique()))}
        df_clean['species'] = df_clean['species'].map(species_mapping)
        
        # Guardamos los datos limpios en una nueva tabla
        df_clean.to_sql('iris_cleaned', engine, if_exists='replace', index=False)
        print(f"Datos limpios y guardados en 'iris_cleaned'. Mapeo de especies: {species_mapping}")

    @task
    def train_model():
        engine = create_engine('mysql+pymysql://taller-airflow:mysql@mysql/taller')
        
        # Leemos los datos limpios desde la tabla 'iris_cleaned'
        df = pd.read_sql_table('iris_cleaned', engine)
        
        # Preparamos las variables: X con las características y y con la variable target ('species')
        X = df.drop(columns=['species'])
        y = df['species']
        
        # Entrenamos un modelo (por ejemplo, RandomForest)
        model = RandomForestClassifier()
        model.fit(X, y)
        
        model_dir = "/opt/airflow/artifacts"
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, "iris_model.joblib")
        joblib.dump(model, model_path)
        print(f"Modelo entrenado y guardado en {model_path}.")

    clean_data_task = clean_data()
    train_model_task = train_model()

    clean_data_task >> train_model_task

clean_train_and_upload_dag = clean_train_and_upload_iris_data()
