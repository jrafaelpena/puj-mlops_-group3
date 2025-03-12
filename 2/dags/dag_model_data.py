from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
import pandas as pd
from sqlalchemy import create_engine
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os

@dag(
    dag_id="train_iris_model",
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False
)
def train_iris_model():
    
    @task
    def train():
        engine = create_engine('mysql+pymysql://taller-airflow:mysql@mysql/taller')
        df = pd.read_sql_table('iris_preprocessed', engine)
        
        X = df[['sepal_length', 'sepal_width', 'petal_length', 'petal_width']]
        y = df['species']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"Exactitud del modelo: {acc}")
        
        model_dir = '/opt/airflow/models'
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'iris_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"Modelo guardado en: {model_path}")
    
    train()

train_iris_model_dag = train_iris_model()
