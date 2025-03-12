from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
import pandas as pd
from sqlalchemy import create_engine

@dag(
    dag_id="preprocess_iris_data",
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False
)
def preprocess_iris_data():
    
    @task
    def preprocess():
        engine = create_engine('mysql+pymysql://taller-airflow:mysql@mysql/taller')
        
        df = pd.read_sql_table('iris_raw', engine)
        
        df_clean = df.dropna()
        
        df_clean.to_sql('iris_preprocessed', engine, if_exists='replace', index=False)
        print("Preprocesamiento completado y datos guardados en 'iris_preprocessed'.")
    
    preprocess()

preprocess_iris_dag = preprocess_iris_data()
