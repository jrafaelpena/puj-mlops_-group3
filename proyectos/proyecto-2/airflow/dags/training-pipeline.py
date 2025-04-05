# Airflow imports
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator

import requests
import pandas as pd
from sqlalchemy import create_engine, text
import os
from datetime import datetime
import time

from sklearn.model_selection import train_test_split
from utils import *
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score
import mlflow

# Parámetros para conexión MySQL
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_DB = os.getenv('MYSQL_DATABASE', 'train_data')
MYSQL_USER = os.getenv('MYSQL_USER', 'airflow')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'airflow')
CONNECTION_STRING = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Parámetros para carga de data del API
GROUP_NUMBER = 3
WAITING_TIME = 32

# Parámetros MLFLOW
TRACKING_URI = "http://mlflow:5000"

os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://minio:9000"
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'


@dag(
    dag_id='1-forest_cover_training-pipeline',
    start_date=days_ago(1),
    schedule_interval="@once",
    catchup=False
)
def training_pipeline():

    @task
    def extract_data():
        print("Truncando forest_cover_data")

        # Create engine properly
        engine = create_engine(CONNECTION_STRING)
        with engine.connect() as connection:
            connection.execute(text("TRUNCATE TABLE forest_cover_data"))
        
        print("La tabla forest_cover_data ha sido truncada exitosamente.")

        # API calls remain the same
        api_refresh_url = f'http://10.43.101.189:80/restart_data_generation?group_number={GROUP_NUMBER}'
        restart_response = requests.get(api_refresh_url)

        if restart_response.status_code == 200:
            print(f'Información del grupo {GROUP_NUMBER} reiniciada exitosamente.')
        else:
            print(f"Error al reiniciar data del API: {restart_response.status_code} - {restart_response.text}")

        for i in range(11):
            print(f"Cargando información de la iteración {i}")
            api_url = f'http://10.43.101.189:80/data?group_number={GROUP_NUMBER}'
            response = requests.get(api_url)

            if response.status_code == 200:
                data = response.json()
                batch_number = data.get('batch_number')
                print(f"Se ha logrado extraer con éxito la data en la iteración {i} del lote {batch_number}")
                raw_data = data.get('data', [])
                
                # DataFrame creation and processing remains the same
                df = pd.DataFrame(raw_data, columns=[ 
                    'Elevation', 'Aspect', 'Slope', 'Horizontal_Distance_To_Hydrology',
                    'Vertical_Distance_To_Hydrology', 'Horizontal_Distance_To_Roadways',
                    'Hillshade_9am', 'Hillshade_Noon', 'Hillshade_3pm',
                    'Horizontal_Distance_To_Fire_Points', 'Wilderness_Area',
                    'Soil_Type', 'Cover_Type'
                ])
                
                numeric_columns = [
                    'Elevation', 'Aspect', 'Slope', 'Horizontal_Distance_To_Hydrology',
                    'Vertical_Distance_To_Hydrology', 'Horizontal_Distance_To_Roadways',
                    'Hillshade_9am', 'Hillshade_Noon', 'Hillshade_3pm',
                    'Horizontal_Distance_To_Fire_Points'
                ]
                df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
                
                df['batch_number'] = batch_number
                df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                try:
                    df.to_sql('forest_cover_data', con=engine, if_exists='append', index=False, chunksize=1000)
                    print(f"Iteración #{i}: Lote {batch_number} guardado exitosamente. {len(df)} registros procesados.")
                except Exception as e:
                    raise ValueError(f"Error al guardar datos en la iteración {i} del lote {batch_number} en MySQL: {e}")
            else:
                print(f"Error al llamar a la API: {response.status_code} - {response.text}")
            
            time.sleep(WAITING_TIME)

    @task
    def train_model():
        print("Empezando proceso de entrenamiento del modelo")
        
        # Se conceta a la base de datos con el connectin string ya creado
        engine = create_engine(CONNECTION_STRING)
        query = "SELECT * FROM forest_cover_data"
        
        try:
            df = pd.read_sql(query, engine)
            print(f"Se cargaron exitosamente {len(df)} registros")
            
            # Remover columnas externas relacioanadas a la metadata de la extracción del API
            df = df.drop(['id', 'batch_number', 'timestamp'], axis=1, errors='ignore')
            
            # Remover columnas categóricas para facilitar la inferencia
            categorical_columns = ['Wilderness_Area', 'Soil_Type']
            df = df.drop(categorical_columns, axis=1)
            
            # Separar features y target
            X = df.drop('Cover_Type', axis=1)
            y = df['Cover_Type']
            
            # Aplicar división del dataset para train y test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            print(f"Training set size: {X_train.shape[0]} samples")
            print(f"Test set size: {X_test.shape[0]} samples")

            # Definir el tracking uri
            tracking_uri = "http://10.43.101.189:5000"
            mlflow.set_tracking_uri(tracking_uri)

            # Crear experimento
            experiment_name = "forest_cover_project_2"
            mlflow.set_experiment(experiment_name)

            run_name = "RandomForestClassifier optimizando Accuracy"
            exp_id = mlflow.get_experiment_by_name("experiment_name")

            with mlflow.start_run(experiment_id=exp_id, run_name=run_name, nested=True):

                study = optuna.create_study(direction="maximize")
                
                study.optimize(
                    make_objective_rf_acc(X_train, y_train),
                    n_trials=20,
                    callbacks=[champion_callback]
                )

                mlflow.log_params(study.best_params)
                mlflow.log_metric("best_accuracy", study.best_value)

                mlflow.set_tags(
                    tags={
                        "project": "Taller MLFlow",
                        "optimizer_engine": "optuna",
                        "model_family": "RandomForestClassifier",
                        "Optimization metric": "Accuracy",
                    }
                )

                model = RandomForestClassifier(**study.best_params, random_state=42, n_jobs=-1)
                model.fit(X_train, y_train)
                
                test_metrics = custom_reports(model, X_test, y_test)
                mlflow.log_metrics(test_metrics)

                artifact_path = "model_rf_acc"

                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path=artifact_path,
                    metadata={"model_data_version": 1},
                )

            run_name = "RandomForestClassifier optimizando AUROC"
            exp_id = mlflow.get_experiment_by_name("experiment_name")

            with mlflow.start_run(experiment_id=exp_id, run_name=run_name, nested=True):

                study = optuna.create_study(direction="maximize")
                

                study.optimize(
                    make_objective_rf_auroc(X_train, y_train),
                    n_trials=20,
                    callbacks=[champion_callback]
                )

                mlflow.log_params(study.best_params)
                mlflow.log_metric("best_auroc", study.best_value)

                mlflow.set_tags(
                    tags={
                        "project": "Taller MLFlow",
                        "optimizer_engine": "optuna",
                        "model_family": "RandomForestClassifier",
                        "Optimization metric": "AUROC",
                    }
                )

                model = RandomForestClassifier(**study.best_params, random_state=42, n_jobs=-1)
                model.fit(X_train, y_train)
                
                test_metrics = custom_reports(model, X_test, y_test)
                mlflow.log_metrics(test_metrics)

                artifact_path = "model_rf_auroc"

                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path=artifact_path,
                    metadata={"model_data_version": 1},
                )
                        
        except Exception as e:
            print(f"Error in train_model task: {e}")
            raise

    extract_data() >> train_model()

training_pipeline_dag = training_pipeline()