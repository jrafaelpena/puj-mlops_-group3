from airflow import DAG
from airflow.models import Variable
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

MAX_EXECUTIONS = 5
DAG_ID = "prueba_schedule_SkipException"

def check_execution_count():
    execution_count = int(Variable.get(f"executions", default_var="0"))

    if execution_count >= MAX_EXECUTIONS:
        raise AirflowSkipException(f"Max executions {MAX_EXECUTIONS} reached.")

    Variable.set(f"executions", str(execution_count + 1))

# Define the DAG
dag = DAG(
    DAG_ID,
    default_args={"owner": "airflow"},
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(seconds=15),
    catchup=False,  # Avoids backfilling old dates
)

check_task = PythonOperator(
    task_id="check_execution_count",
    python_callable=check_execution_count,
    dag=dag,
)