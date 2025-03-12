from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
import pandas as pd
from sqlalchemy import create_engine

@dag(
    dag_id="clean-upload-iris",
    start_date=days_ago(1),
    schedule_interval="@once",
    catchup=False
)
def clean_and_upload_iris_data():
    
    @task
    def clean_data():
        engine = create_engine('mysql+pymysql://taller-airflow:mysql@mysql/taller')
        
        # Leemos los datos preprocesados (puedes cambiar a 'iris_raw' según convenga)
        df = pd.read_sql_table('iris_raw', engine)
        
        # Realizamos una limpieza adicional, por ejemplo, eliminamos duplicados y filas con NaN
        df_clean = df.drop_duplicates().dropna()
        
        # Guardamos los datos limpios en una nueva tabla, por ejemplo 'iris_cleaned'
        df_clean.to_sql('iris_cleaned', engine, if_exists='replace', index=False)
        print("Datos limpios y guardados en 'iris_cleaned'.")
    
    clean_data()

clean_and_upload_dag = clean_and_upload_iris_data()
