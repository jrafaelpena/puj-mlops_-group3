from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

@dag(
    dag_id="4-train-model",
    start_date=days_ago(1),
    schedule_interval="@once",
    catchup=False
)
def train_and_extract_model():
    
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
        
        # Definimos la carpeta donde se guardará el modelo
        model_folder = '/opt/airflow/models'
        os.makedirs(model_folder, exist_ok=True)
        model_path = os.path.join(model_folder, 'iris_model.pkl')
        
        # Guardamos el modelo utilizando pickle
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"Modelo entrenado y guardado en {model_path}.")
    
    train_model()

train_model_dag = train_and_extract_model()
