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

from io import StringIO

# Parámetros para conexión PostgreSQL
POSTGRES_HOST = "10.43.101.189"
POSTGRES_PORT = "31543"
POSTGRES_DB = "train_data"
POSTGRES_USER = "project3"
POSTGRES_PASSWORD = "project3"

# SQLAlchemy connection string for PostgreSQL
CONNECTION_STRING = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


# Parámetros MLFLOW
TRACKING_URI = "http://10.43.101.189:30010"

os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://10.43.101.189:30000"
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'project3'

@task
def extract_data():
    engine = create_engine(CONNECTION_STRING)
    print('Engine created')

    # Step 1: Drop and create the raw_data table
    sql_path = os.path.join(os.path.dirname(__file__), "raw_data_creation.sql")
    with open(sql_path, 'r') as file:
        creation_query = file.read()

    print('Dropping raw_data table and creating it')
    with engine.connect() as conn:
        conn.execute(text(creation_query))
    print('raw_data created')

    # Step 2: Download CSV content into memory
    url = 'https://docs.google.com/uc?export=download&confirm=&id=1k5-1caezQ3zWJbKaiMULTGq-3sz6uThC'
    print('Downloading dataset into memory...')
    response = requests.get(url, allow_redirects=True, stream=True)
    response.raise_for_status()  # Raise error if download fails

    csv_data = StringIO(response.content.decode('utf-8'))

    # Step 3: Load into DataFrame
    print('Reading CSV to DataFrame...')
    df = pd.read_csv(csv_data)

    # Normalize column names to match the DB schema
    df.columns = [col.replace('-', '_') for col in df.columns]

    # Step 4: Insert in batches of 15,000
    batch_size = 15000
    total_rows = len(df)
    print(f'Inserting {total_rows} rows into raw_data in batches of {batch_size}')

    for i in range(0, total_rows, batch_size):
        batch_df = df.iloc[i:i + batch_size]
        batch_df.to_sql("raw_data", con=engine, if_exists="append", index=False)
        print(f'Inserted rows {i} to {i + len(batch_df) - 1}')

    print('All data inserted successfully')