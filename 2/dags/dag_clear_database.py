from airflow.decorators import task, dag
from airflow.utils.dates import days_ago
from datetime import datetime
import mysql.connector

@dag(
    dag_id='clear_database',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False
)
def clear_database_dag():
    
    @task
    def clear_database(**kwargs):
        from airflow.models import TaskInstance

        ti: TaskInstance = kwargs['ti']
        log = ti.log

        db_config = {
            "host": "mysql",
            "user": "taller-airflow",
            "password": "mysql",
            "database": "taller",
        }
        
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS iris_raw;")
                conn.commit()

        log.info("Table 'iris_raw' dropped successfully (if it existed).")

    clear_database()

clear_db_dag = clear_database_dag()
