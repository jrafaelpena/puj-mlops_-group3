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


@dag(
    dag_id='1-diabetes-training-pipeline',
    start_date=days_ago(1),
    schedule_interval="@once",
    catchup=False
)
def training_pipeline():
    
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
        df.columns = [col.lower().replace('-', '_') for col in df.columns]

        # Step 4: Insert in batches of 15,000
        batch_size = 15000
        total_rows = len(df)
        print(f'Inserting {total_rows} rows into raw_data in batches of {batch_size}')

        for i in range(0, total_rows, batch_size):
            batch_df = df.iloc[i:i + batch_size]
            batch_df.to_sql("raw_data", con=engine, if_exists="append", index=False)
            print(f'Inserted rows {i} to {i + len(batch_df) - 1}')

        print('All data inserted successfully')

    @task
    def preprocess_and_split():
        engine = create_engine(CONNECTION_STRING)
        df = pd.read_sql("SELECT * FROM raw_data", con=engine)

        # 1. Columns with more than 40% nulls
        high_null_cols = df.columns[df.isnull().mean() > 0.40].tolist()

        # 2. Columns containing '_id' or named 'patient_nbr'
        id_columns = [col for col in df.columns if '_id' in col.lower()] + ['patient_nbr']

        # 3. High cardinality object columns (more than 10 unique values)
        high_cardinality_cols = [
            col for col in df.select_dtypes(include='object').columns 
            if df[col].nunique() > 10
        ]

        # 4. Low variance columns: fewer than 5 unique values and top value > 80%
        low_variance_cols = [
            col for col in df.columns 
            if df[col].nunique(dropna=False) < 5 and df[col].value_counts(normalize=True, dropna=False).values[0] > 0.80
        ]

        # Final set of columns to drop
        columns_to_drop = list(set(
            high_null_cols + id_columns + high_cardinality_cols + low_variance_cols
        ))
        df = df.drop(columns=columns_to_drop)

        # Fill remaining nulls
        df = df.fillna('Unknown')

        # Stratified split for the target column `readmitted`
        train_df, temp_df = train_test_split(df, stratify=df['readmitted'], test_size=0.4, random_state=42)
        val_df, test_df = train_test_split(temp_df, stratify=temp_df['readmitted'], test_size=0.5, random_state=42)

        train_df['dataset'] = 'train'
        val_df['dataset'] = 'validation'
        test_df['dataset'] = 'test'

        final_df = pd.concat([train_df, val_df, test_df])

        # Save to new table
        final_df.to_sql("clean_data", con=engine, if_exists="replace", index=False)

        print("Preprocessing completed. clean_data table created with shape:", final_df.shape)

    
    extract_data() >> preprocess_and_split()

training_pipeline_dag = training_pipeline()
