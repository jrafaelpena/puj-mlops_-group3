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
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

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

# Parámetros entrenamiento
ITERATIONS = 5

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

        # 1. Columns with more than 50% nulls
        high_null_cols = df.columns[df.isnull().mean() > 0.5].tolist()

        # 2. Columns containing '_id' or named 'patient_nbr'
        id_columns = [col for col in df.columns if '_id' in col.lower()] + ['patient_nbr']

        # 3. High cardinality object columns (more than 35 unique values)
        high_cardinality_cols = [
            col for col in df.select_dtypes(include='object').columns 
            if df[col].nunique() > 35
        ]

        # 4. Low variance columns: one category represents more than 90% of the values
        low_variance_cols = [
            col for col in df.columns 
            if df[col].value_counts(normalize=True, dropna=False).values[0] > 0.9
        ]

        # Combine all into a set to avoid duplicates
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

    @task
    def train_model_accuracy():
        print("Starting model training process for diabetes dataset")

        engine = create_engine(CONNECTION_STRING)
        query = "SELECT * FROM clean_data WHERE dataset IN ('train', 'test')"

        try:
            df = pd.read_sql(query, engine)
            print(f"Successfully loaded {len(df)} records")

            # Separate features and target
            X = df.drop(['readmitted', 'dataset'], axis=1)
            y = df['readmitted']

            # Detect categorical and numerical columns
            cat_cols = X.select_dtypes(include='object').columns.tolist()
            num_cols = X.select_dtypes(exclude='object').columns.tolist()

            # Split into train and test
            train_mask = df['dataset'] == 'train'
            test_mask = df['dataset'] == 'test'
            X_train, X_test = X[train_mask], X[test_mask]
            y_train, y_test = y[train_mask], y[test_mask]

            print(f"Train samples: {X_train.shape[0]} | Test samples: {X_test.shape[0]}")

            mlflow.set_tracking_uri(TRACKING_URI)
            experiment_name = "diabetes_prediction"
            mlflow.set_experiment(experiment_name)
            experiment = mlflow.get_experiment_by_name(experiment_name)

            # Preprocessing pipeline
            preprocessor = ColumnTransformer([
                ("cat", OneHotEncoder(handle_unknown='ignore'), cat_cols)
            ], remainder='passthrough')

            with mlflow.start_run(experiment_id=experiment.experiment_id, run_name="Optimizing Accuracy", nested=True):
                study = optuna.create_study(direction="maximize")

                study.optimize(
                    make_objective_rf_acc(X_train, y_train, preprocessor),
                    n_trials=ITERATIONS,
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

                final_pipeline = Pipeline([
                ("preprocess", preprocessor),
                ("model", RandomForestClassifier(**study.best_params, random_state=42, n_jobs=-1))
                ])

                final_pipeline.fit(X_train, y_train)

                metrics = custom_reports(final_pipeline, X_test, y_test)
                mlflow.log_metrics(metrics)

                artifact_path = "model_rf_accuracy"

                mlflow.sklearn.log_model(
                    final_pipeline,
                    artifact_path=artifact_path,
                    metadata={"model_data_version": 1}
                )
        except Exception as e:
            print(f"Error in train_model_accuracy: {e}")
            raise
 
    @task
    def train_model_auroc():
        print("Starting model training process for diabetes dataset")

        engine = create_engine(CONNECTION_STRING)
        query = "SELECT * FROM clean_data WHERE dataset IN ('train', 'test')"

        try:
            df = pd.read_sql(query, engine)
            print(f"Successfully loaded {len(df)} records")

            # Separate features and target
            X = df.drop(['readmitted', 'dataset'], axis=1)
            y = df['readmitted']

            # Detect categorical and numerical columns
            cat_cols = X.select_dtypes(include='object').columns.tolist()
            num_cols = X.select_dtypes(exclude='object').columns.tolist()

            # Split into train and test
            train_mask = df['dataset'] == 'train'
            test_mask = df['dataset'] == 'test'
            X_train, X_test = X[train_mask], X[test_mask]
            y_train, y_test = y[train_mask], y[test_mask]

            print(f"Train samples: {X_train.shape[0]} | Test samples: {X_test.shape[0]}")

            mlflow.set_tracking_uri(TRACKING_URI)
            experiment_name = "diabetes_prediction"
            mlflow.set_experiment(experiment_name)
            experiment = mlflow.get_experiment_by_name(experiment_name)

            # Preprocessing pipeline
            preprocessor = ColumnTransformer([
                ("cat", OneHotEncoder(handle_unknown='ignore'), cat_cols)
            ], remainder='passthrough')

            with mlflow.start_run(experiment_id=experiment.experiment_id, run_name="Optimizing AUROC", nested=True):
                study = optuna.create_study(direction="maximize")

                study.optimize(
                    make_objective_rf_auroc(X_train, y_train, preprocessor),
                    n_trials=ITERATIONS,
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

                final_pipeline = Pipeline([
                ("preprocess", preprocessor),
                ("model", RandomForestClassifier(**study.best_params, random_state=42, n_jobs=-1))
                ])

                final_pipeline.fit(X_train, y_train)

                metrics = custom_reports(final_pipeline, X_test, y_test)
                mlflow.log_metrics(metrics)

                artifact_path = "model_rf_auroc"

                mlflow.sklearn.log_model(
                    final_pipeline,
                    artifact_path=artifact_path,
                    metadata={"model_data_version": 1}
                )
        except Exception as e:
            print(f"Error in train_model_accuracy: {e}")
            raise

    extract_data() >> preprocess_and_split() >> [train_model_accuracy(), train_model_auroc()]

training_pipeline_dag = training_pipeline()