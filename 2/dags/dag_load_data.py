from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

def load_iris_data():
    # Load the Iris dataset from Seaborn
    iris = pd.read_csv('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv')
    
    # Create database connection
    engine = create_engine('mysql+pymysql://taller-airflow:mysql@mysql/taller')
    
    # Load to MySQL database
    iris.to_sql('iris_raw', engine, if_exists='replace', index=False)

# Define the DAG
with DAG('load_iris_data', 
         start_date=datetime(2023, 1, 1), 
         schedule_interval=None, 
         catchup=False) as dag:
    
    load_data_task = PythonOperator(
        task_id='load_iris_data',
        python_callable=load_iris_data
    )
