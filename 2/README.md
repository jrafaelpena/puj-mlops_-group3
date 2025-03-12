# Taller Airflow

Al archivo `docker-compose.yaml` que inicialmente estaba hecho para levantar la arquitectura de Airflow, se el agregaron los siguientes servicios:
- **mysql**: Instancia con servidor de MySql para no usar la base de Postgres para procesos de entrenamiento.

Se agregaron los siguientes DAGs:
- **1-clear-database** (`dag_clear_database.py`): Este elimina la tabla `iris_raw` de la base de datos como se indicó en el taller. En este DAG no se usa un tipo de operador específico, se usa el TaskFlow API para definir tareas como funciones con `@task`, en lugar de `PythonOperator` u otros operadores tradicionales, mostrando una alternativa basada en decoradores, la cual es recomendada en las versiones más recientes de Airflow.
- **2-load-iris-data** (`dag_load_data.py`): Este DAG se encarga de leer el dataset de iris y cargarlo en la base de datos con el nombre `iris_raw`.  En este DAG se utiliza `PythonOperator` para definir las tareas. Este enfoque permite ejecutar funciones de Python mediante operadores explícitos, ofreciendo mayor flexibilidad en la configuración de parámetros y dependencias.
- **3-clean-upload-iris** (`dag_clean_data.py`): En este caso, la tarea clean_data lee datos desde una base de datos MySQL, los limpia eliminando duplicados y valores nulos, y los guarda en una nueva tabla.
- **4-train-model** (`dag_model_data`):La tarea `train_model` lee datos limpios desde una base de datos MySQL, entrena un modelo de clasificación utilizando `RandomForestClassifier`, y guarda el modelo entrenado en un archivo local con pickle, permitiendo su posterior uso en predicciones o despliegue.









