from datetime import datetime, timedelta
import requests
import pandas as pd
from sqlalchemy import create_engine, text
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# Argumentos por defecto
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}
Variable.set("execution_counter", 0)

# Creación del DAG
dag = DAG(
    'prueba_schedule_intervals',
    default_args=default_args,
    description='Prueba para entender mejor la lógica de schedule_interval',
    start_date=datetime(2025, 4, 2),
    schedule_interval=timedelta(seconds=30),
    catchup=False,
    max_active_runs=1,
)

def print_message():
    print("Ejecutando tarea de prueba para validar el intervalo de ejecución de 30 segundos")
    execution_number = int(Variable.get("execution_counter")) + 1
    Variable.set("execution_counter", execution_number)
    print(execution_number)

print_task = PythonOperator(
    task_id='print_message',
    python_callable=print_message,
    dag=dag,
)

print_task