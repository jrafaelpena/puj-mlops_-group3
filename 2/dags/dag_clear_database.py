from airflow.decorators import task, dag
from airflow.utils.dates import days_ago
from datetime import datetime
import mysql.connector

@dag(
    dag_id='1-clear-database',
    start_date=days_ago(1),
    schedule_interval="@once",
    catchup=False
)
def clear_database_dag():
    
    @task
    def clear_database(**kwargs):

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

        print("Table 'iris_raw' dropped successfully (if it existed).")

    clear_database()

clear_db_dag = clear_database_dag()
