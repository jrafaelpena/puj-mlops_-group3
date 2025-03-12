from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.utils.dates import days_ago

with DAG(
    dag_id="ssh_context_dag",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
) as dag:

    ssh_task = SSHOperator(
        task_id="run_preprocess",
        ssh_conn_id="jupyter",
        command="uv run /work/preprocess.py",
    )

    ssh_task
