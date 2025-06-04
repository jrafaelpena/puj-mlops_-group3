# Airflow imports
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

import requests
import pandas as pd
from sqlalchemy import create_engine, text
import os
from datetime import datetime
import time

from sklearn.model_selection import train_test_split
from utils import *
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import mlflow

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


# Parámetros para conexión PostgreSQL
POSTGRES_HOST = "10.43.101.189"
POSTGRES_PORT = "31543"
POSTGRES_DB = "train_data"
POSTGRES_USER = "project4"
POSTGRES_PASSWORD = "project4"

# SQLAlchemy connection string for PostgreSQL
CONNECTION_STRING = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


# Parámetros MLFLOW
TRACKING_URI = "http://10.43.101.189:30010"

os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://10.43.101.189:30000"
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'project3'


# Parámetros API inferencia
INFERENCE_API_URL = "http://10.43.101.189:30898/load_model/"

# Parámetros entrenamiento
DATA_API_URL = "http://10.43.101.108:80/data"
DATA_API_URL_PARAMS = {
    "group_number": 3,
    "day": "Wednesday"
} 
MAX_API_BATCH = 5

@dag(
    dag_id='1-house-prices-training-pipeline',
    start_date=days_ago(1),
    schedule_interval="@once",
    catchup=False,
    max_active_runs=1
)
def training_pipeline():

    @task
    def evaluate_run_and_load_raw_data() -> int:
        # Initiate request to external Data API to fetch the latest batch of house price data
        print("Sending GET request to Data API...")
        response = requests.get(DATA_API_URL, params=DATA_API_URL_PARAMS)

        # Check if the API call was successful
        if response.status_code == 200:
            response_json = response.json()

            # Extract batch number from the API response for tracking
            batch = response_json['batch_number']
            print(f"Successfully retrieved data for batch number: {batch}")

            # Initialize SQLAlchemy engine for database interactions
            engine = create_engine(CONNECTION_STRING)
            print("Database engine created successfully.")

            # If this is the first batch, reset the raw_data and clean_data tables
            if batch == 0:
                print("Batch 0 detected - resetting raw_data and clean_data tables.")
                sql_path = os.path.join(os.path.dirname(__file__), "raw_data_creation.sql")
                with open(sql_path, 'r') as file:
                    creation_query = file.read()

                # Execute the SQL commands to reset tables
                with engine.connect() as conn:
                    conn.execute(text(creation_query))
                print("Tables 'raw_data' and 'clean_data' have been reset successfully.")

            # Extract the actual data records from the API response
            records = response_json["data"]

            # Create a Pandas DataFrame from the list of records
            df = pd.DataFrame(records)

            # Enforce correct data types for each column to maintain consistency
            df = df.astype({
                'brokered_by': 'int64',
                'status': 'string',
                'price': 'float64',
                'bed': 'int64',
                'bath': 'int64',
                'acre_lot': 'float64',
                'street': 'string',
                'city': 'string',
                'state': 'string',
                'zip_code': 'string',
                'house_size': 'int64'
            })

            # Lowercase normalization for city and state columns
            df['city'] = df['city'].str.lower()
            df['state'] = df['state'].str.lower()

            # Clean street and zip_code columns by removing any trailing ".0"
            df['street'] = df['street'].str.replace(r'\.0$', '', regex=True)
            df['zip_code'] = df['zip_code'].str.replace(r'\.0$', '', regex=True)

            # Convert 'prev_sold_date' column to datetime format, coercing errors to NaT
            df['prev_sold_date'] = pd.to_datetime(df['prev_sold_date'], errors='coerce')

            # Add the batch number as a column for traceability in the database
            df['batch'] = int(batch)

            # Append the new batch of data to the 'raw_data' table in the database
            df.to_sql("raw_data", con=engine, if_exists="append", index=False)
            print(f"Inserted {df.shape[0]} rows into 'raw_data' table from batch {batch}.")

            # Return batch number to pass it to downstream tasks for tracking or further processing
            return batch

        else:
            # Log failure details and raise an exception to stop the pipeline gracefully
            print(f"Failed to fetch data from API. HTTP Status: {response.status_code}")
            print(f"Response content: {response.text}")
            print("No further batches available. Stopping pipeline execution.")
            raise AirflowSkipException("Reached max number of runs.")

    @task
    def preprocess_and_split(batch: int) -> None:
        print(f"Starting preprocessing for batch: {batch}")
        
        engine = create_engine(CONNECTION_STRING)
        print("Database engine created successfully.")

        df = pd.read_sql(f"SELECT * FROM raw_data WHERE batch = {batch}", con=engine)
        print(f"Loaded raw_data for batch {batch}: {df.shape[0]} rows, {df.shape[1]} columns")

        # Drop columns that are not useful or cause leakage
        columns_to_drop = [
            "brokered_by",
            "street",
            "status",
            "prev_sold_date"
        ]
        df = df.drop(columns=columns_to_drop)
        print(f"Dropped columns: {columns_to_drop}")
        print(f"Data shape after dropping columns: {df.shape}")

        # Create price bins for stratification (quartiles)
        df['price_bin'] = pd.qcut(df['price'], q=4, duplicates='drop')
        print(f"Created 'price_bin' column with bins:\n{df['price_bin'].value_counts()}")

        # Perform stratified train-test split
        train_df, test_df = train_test_split(
            df,
            stratify=df['price_bin'],
            test_size=0.15,
            random_state=42
        )
        print(f"Train set size: {train_df.shape[0]}, Test set size: {test_df.shape[0]}")

        # Drop 'price_bin' before saving
        train_df = train_df.drop(columns=['price_bin'])
        test_df = test_df.drop(columns=['price_bin'])

        train_df['dataset'] = 'train'
        test_df['dataset'] = 'test'

        final_df = pd.concat([train_df, test_df])
        print(f"Final dataframe shape after concatenation: {final_df.shape}")

        if_exists = "replace" if batch == 0 else "append"
        print(f"Saving data to 'clean_data' table with if_exists='{if_exists}'")
        
        # FIXED: Use explicit transaction management
        with engine.begin() as conn:
            final_df.to_sql("clean_data", con=conn, if_exists=if_exists, index=False)
            
            # Verify data was written successfully
            row_count = conn.execute(text("SELECT COUNT(*) FROM clean_data")).scalar()
            print(f"Successfully committed {row_count} total rows to clean_data table")
            
            # Verify this batch's data specifically
            batch_count = conn.execute(text(f"SELECT COUNT(*) FROM clean_data WHERE batch = {batch}")).scalar()
            print(f"Batch {batch} contributed {batch_count} rows")
        
        # Clean up connection pool to ensure fresh connections for next task
        engine.dispose()
        print(f"Preprocessing completed. clean_data table updated with batch: {batch}")

    @task
    def train_decesision(batch: int) -> bool:
        print(f"Starting train_decesision task for batch: {batch}")

        engine = create_engine(CONNECTION_STRING)
        print("Database engine created successfully.")

        if batch == 0:
            # For batch 0, always train and record batch 0 as processed
            train_boolean = True
            new_batches = [0]
            print("Batch is 0, training automatically triggered.")

            # Create or overwrite batches_check table with batch 0
            batches_check_new = pd.DataFrame({'batch': new_batches})
            batches_check_new.to_sql("batches_check", con=engine, if_exists="replace", index=False)
            print("batches_check table initialized with batch 0.")
        else:
            # Load already processed batches from batches_check table
            query = "SELECT * FROM batches_check"
            batches_check = pd.read_sql(query, engine)
            batches_current_model = batches_check['batch'].astype("Int32").to_list()
            print(f"Loaded batches_check: {batches_current_model}")

            # Load all clean data
            query = "SELECT * FROM clean_data"
            engine_2 = create_engine(CONNECTION_STRING)
            clean_data_df = pd.read_sql(query, engine_2)
            print(f"Loaded clean_data with {clean_data_df.shape[0]} rows")

            # Find batches not yet processed
            new_batches = clean_data_df.loc[
                ~clean_data_df['batch'].astype("Int32").isin(batches_current_model), 'batch'
            ].unique().tolist()
            print(f"Identified new batches: {new_batches}")

            # Count rows for batches already processed and for new batches
            total_rows_base = clean_data_df[
                clean_data_df['batch'].astype("Int32").isin(batches_current_model)
            ].shape[0]
            total_rows_new = clean_data_df[
                clean_data_df['batch'].astype("Int32").isin(new_batches)
            ].shape[0]
            total_rows_all = clean_data_df.shape[0]
            print(f"Rows in existing batches: {total_rows_base}")
            print(f"Rows in new batches: {total_rows_new}")
            print(f"Total rows in clean_data: {total_rows_all}")

            proportion_new = total_rows_new / total_rows_all if total_rows_all > 0 else 0
            print(f"Proportion of new data: {proportion_new:.2f}")

            train_boolean = proportion_new >= 0.6
            print(f"Training decision: {'Yes' if train_boolean else 'No'}")

            if train_boolean:
                print(f"Training is necessary at batch {batch}: New batches for training: {new_batches}")

                # Update batches_check table with the new batches added
                updated_batches = sorted(set(batches_current_model) | set(new_batches))
                batches_check_new = pd.DataFrame({'batch': updated_batches})
                batches_check_new.to_sql("batches_check", con=engine, if_exists="replace", index=False)
                print("batches_check table updated successfully.")

        print(f"train_decesision task completed with train_boolean={train_boolean}")
        return train_boolean

    @task
    def train_model(train_boolean: bool, batch: int) -> None:
        if not train_boolean:
            print(f"[Batch {batch}] Skipping training: train_boolean is False")
            return None

        print(f"[Batch {batch}] Starting training pipeline...")

        # Create DB engine and load train/test data
        engine = create_engine(CONNECTION_STRING)
        query = "SELECT * FROM clean_data WHERE dataset = '{}'"
        
        print("[Data] Loading train dataset from database...")
        train_df = pd.read_sql(query.format("train"), engine)
        print(f"[Data] Train dataset loaded with shape: {train_df.shape}")
        
        print("[Data] Loading test dataset from database...")
        test_df = pd.read_sql(query.format("test"), engine)
        print(f"[Data] Test dataset loaded with shape: {test_df.shape}")

        # Feature/target split
        columns_to_drop_x = ['batch', 'dataset', 'price']
        X_train = train_df.drop(columns=columns_to_drop_x)
        y_train = train_df['price']

        X_test = test_df.drop(columns=columns_to_drop_x)
        y_test = test_df['price']

        # Define categorical features for one-hot encoding
        cat_columns = ['city', 'state', 'zip_code']
        print(f"[Preprocessing] Applying OneHotEncoder to: {cat_columns}")

        one_hot_encoder = OneHotEncoder(
            max_categories=51,
            min_frequency=0.001,
            handle_unknown='infrequent_if_exist'
        )

        preprocessor = ColumnTransformer([
            ("one_hot_encoder", one_hot_encoder, cat_columns)
        ], remainder='passthrough', force_int_remainder_cols=False)

        # Final pipeline with preprocessing and model
        final_pipeline = Pipeline([
            ("preprocess", preprocessor),
            ("model", LinearRegression(n_jobs=-1))
        ])

        print("[Training] Fitting the pipeline on training data...")
        final_pipeline.fit(X_train, y_train)
        print("[Training] Pipeline training complete.")

        # Set up MLflow
        mlflow.set_tracking_uri(TRACKING_URI)
        experiment_name = "house_price_prediction"
        mlflow.set_experiment(experiment_name)
        experiment = mlflow.get_experiment_by_name(experiment_name)

        print(f"[MLflow] Logging model for batch {batch}...")

        with mlflow.start_run(experiment_id=experiment.experiment_id, run_name=f"run_batch_{batch}") as run:
            # Custom evaluation and metrics logging
            metrics = custom_reports_regression(final_pipeline, X_test, y_test)
            print(f"[Metrics] Logged metrics: {metrics}")
            mlflow.log_metrics(metrics)

            # Log the trained model
            artifact_path = f"model_rf_batch_{batch}"
            mlflow.sklearn.log_model(
                final_pipeline,
                artifact_path=artifact_path,
                registered_model_name='house_prices'
            )
            print(f"[MLflow] Model logged under: {artifact_path}")

        # Register model as champion/challenger
        client = mlflow.MlflowClient()
        new_model_version = int(client.search_model_versions("name='house_prices'")[0].version)

        new_model_alias = 'champion' if batch == 0 else 'challenger'
        client.set_registered_model_alias("house_prices", new_model_alias, new_model_version)
        print(f"[MLflow] Model version {new_model_version} assigned alias '{new_model_alias}'")

        # Model comparison step
        if batch != 0:
            print("[Model Selection] Comparing challenger with current champion...")

            # Load champion model
            try:
                champion_model = mlflow.pyfunc.load_model("models:/house_prices@champion")
                champion_version = client.get_model_version_by_alias("house_prices", "champion").version
            except Exception as e:
                print(f"[Warning] Could not load champion model: {e}")
                print(f"[Warning] Assigning @champion alias to new version: {new_model_version}")
                client.set_registered_model_alias("house_prices", 'champion', new_model_version)
                return  # Exit early if no champion to compare against

            # Evaluate both models
            champion_model_metrics = custom_reports_regression(champion_model, X_test, y_test)

            print(f"[Comparison] Champion (v{champion_version}) metrics: {champion_model_metrics}")
            print(f"[Comparison] Challenger (v{new_model_version}) metrics: {metrics}")

            with mlflow.start_run(run_name=f"comparison_champion_v{champion_version}_challenger_v{new_model_version}"):
                mlflow.log_metrics({f"champion_{k}": v for k, v in champion_model_metrics.items()})
                mlflow.log_metrics({f"challenger_{k}": v for k, v in metrics.items()})

            # Promote challenger if it has better or equal RMSE
            if metrics['test_rmse'] <= champion_model_metrics['test_rmse']:
                client.set_registered_model_alias("house_prices", 'champion', new_model_version)
                print(f"[Promotion] Challenger promoted to champion (v{new_model_version})")
                print(f"Calling 'inference-api/load_model' method")
            else:
                print(f"[Promotion] Champion model (v{champion_version}) retained")

        print(f"[Batch {batch}] Training task completed successfully.")

    trigger_rerun = TriggerDagRunOperator(
        task_id='trigger_dag_rerun',
        trigger_dag_id='1-house-prices-training-pipeline',  # Same DAG ID
        wait_for_completion=False,  # Don't wait for the triggered run to complete
        trigger_rule='all_done',  # Trigger when all upstream tasks finish (success or failure)
        conf={"triggered_by": "rerun_task"}  # Optional: pass configuration to identify this as a rerun
    )

    batch = evaluate_run_and_load_raw_data()
    preprocess_task = preprocess_and_split(batch)
    train_boolean = train_decesision(batch)
    train_task = train_model(train_boolean, batch)
    
    preprocess_task >> train_boolean >> train_task >> trigger_rerun

training_pipeline_dag = training_pipeline()