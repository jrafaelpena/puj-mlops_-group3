# Taller MLflow

### 1. Agregar servicios de bases de datos en el archivo Docker Compose

Se crea un servicio de base de datos PostgreSQL para ser utilizado por el servicio de MLflow y una base de datos MySQL para la carga de datos de entrenamiento. Para verificar esta creación, revisar el archivo `docker-compose.yaml`.

A continuación se presentan todos los contenedores creados con docker compose activos:

![imagen](images/0-dockercompose.png)

### 2. Crear Bucket en Minio

Se crea el bucket `mlflows3`que será usado por el servicio de MLflow.

![imagen](images/2-creacion_bucket.png)

### 3. Inicializar servicio de MLflow

Antes de iniciar el servicio, se instalan las dependencias necesarias con uv en un entorno virtual dentro de la carpeta del taller:
- `awscli`
- `boto3`
- `mlflow`
- `psycopg2-binary` (Para la conexión con Postgres)

Teniendo las dependencias se hacen los cambios necesarios al archivo `mlflow_serv.service`:

```service
[Unit]
Description=MLflow tracking server
After=network.target 

[Service]
User=estudiante
Restart=on-failure
RestartSec=3
# Cambio: Se define la carpeta correcta
WorkingDirectory=/home/estudiante/curso-mlops/puj-mlops_-group3/2-mlflow
# Cambio: Se define la ip de la máquina virtual asignada
Environment=MLFLOW_S3_ENDPOINT_URL=http://10.43.101.189:9000
Environment=AWS_ACCESS_KEY_ID=admin
Environment=AWS_SECRET_ACCESS_KEY=supersecret
# Cambio: Se defina la ruta al python dentro del entorno virtual creado con uv
ExecStart= /home/estudiante/curso-mlops/puj-mlops_-group3/2-mlflow/.venv/bin/python3 -m mlflow server \
# Cambio: Se define la conexión con la base de datos Postgres
--backend-store-uri postgresql://mlflow_user:mlflow_user@10.43.101.189:5432/mlflow_db \
--default-artifact-root s3://mlflows3/artifacts \
--host 0.0.0.0 \
--serve-artifacts

[Install]
WantedBy=multi-user.target
```

Se confirma que el servicio funcione con los comandos proporcionados por el profesor y además se abre la interfaz web:

![imagen](images/3-interfaz_web_mlflow.png)

### 3. Inicializar servicios de Jupyter y FastApi con otro archivo de docker compose

Se leventan el grupo de servicios por separado y no en el mismo contenedor. Los archivos para el levantamiento están en la carpeta `ml-components` donde se guardan los archivos relacionados a la API y el servidor de jupyter, también separados en carpetas distintas como se observa en el archivo de docker compose:

```yaml
services:
  fastapi:
    build:
      context: ./app
      dockerfile: Dockerfile.fastapi
    
    image: fast-api-mlflow
    
    ports:
      - "8989:8989"

    command: ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8989", "--reload"]

  jupyter:
    build:
      context: ./jupyter-env
      dockerfile: Dockerfile.jupyter
    
    image: jupyter-mlflow

    ports:
      - "8888:8888"

    volumes:
      - './jupyter-env:/work'
```

### 4. Cargue y procesamiento de datos

En el servidor de jupyter, se tiene el archivo `preprocess.py` que tiene todo el código para:

1.  Eliminar la información de la base de datos creada (`taller`)
2.  Leer data externa iris.
3.  Crear la tabla `iris_raw` y cargar la data leída en esta tabla.
4.  Leer la data desde `iris_raw` y realizar preprocesamiento.
5.  Crear la tabla `iris_cleaned` y cargar la data preprocesada en esta tabla.

Se ejecuta `uv run preprocess.py` y se confirma por medio de los prints que el proceso fue exitoso:

![imagen](images/4-limpieza_datos.png)

Para listar las tablas en la base de datos se usa:

```python
# Crear el inspector de la base de datos
inspector = inspect(engine)

# Obtener la lista de tablas en la base de datos 'taller'
tables = inspector.get_table_names()

# Imprimir la lista de tablas
print("Tablas en la base de datos 'taller':", tables)
```
Posteriormente, en el notebook se carga la tabla `iris_cleaned` leída desde la base de datos puesto que es un notebook aparte. Este paso queda omitido de posterior documentación, ya que se asume desde este punto.

### 5. Conexión a MLFlow y creación de experimento

Se define el tracking uri como `http://10.43.101.189:5000` y se crea el experimento `iris_classification_experiment`:

![imagen](images/5-primeros_pasos_mlflow.png)

Y por medio de la interfaz en la web de MLFlow se puede verificar la creación del experimento:

![imagen](images/6-verificaion_experimento.png)

### Entrenamiento con registro del modelo y métricas en MLFlow

Por medio de la [documentación presentada por MLflow para la integración con Optuna](https://mlflow.org/docs/latest/traditional-ml/hyperparameter-tuning-with-child-runs/notebooks/hyperparameter-tuning-with-child-runs/), se realiza la optimización de hiperparámetros con esta librería.

El experimento consiste en usar el modelo `RandomForestClassifier` y generar una búsqueda de hiperparámetros optimizando el accuracy y el AUROC (Area Under the Receiver Operating Characteristic Curve), generando 20 iteraciones para cada métrica. Es decir:

| Algoritmo             | Métrica de optimización | Iteraciones |
|----------------------|------------------------|------------|
| RandomForestClassifier | Accuracy               | 20         |
| RandomForestClassifier | AUROC                  | 20         |

A continuación se muestra el ejemplo de código para la búsqueda usando Tree Parsen Optimization que es el algoritmo de búsqueda default de Optuna:

```python
def objective_rf_acc(trial):
    with mlflow.start_run(nested=True):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 600), 
            'max_depth': trial.suggest_int('max_depth', 3, 30), 
            'min_samples_split': trial.suggest_int('min_samples_split', 3, 20), 
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 3, 20), 
            'max_features': trial.suggest_float('max_features', 0.5, 1.0),
            'max_samples': trial.suggest_float('max_samples', 0.7, 1.0)
        }
        
        # Initialize model
        model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)

        # Define Stratified K-Folds
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        # Compute cross-validation scores using Accuracy
        scores = cross_val_score(model, X, y, cv=skf, scoring="accuracy", n_jobs=-1)
        scores_2 = cross_val_score(model, X, y, cv=skf, scoring="roc_auc_ovo", n_jobs=-1)

        # Log parameters and metrics
        mlflow.log_params(params)
        mlflow.log_metric("mean_accuracy", np.mean(scores))
        mlflow.log_metric("mean_auroc", np.mean(scores_2))

        return np.mean(scores)
```

Y la finalización del modelo seleccionando la mejor combinación:

```python
run_name = "RandomForestClassifier optimizando Accuracy"
exp_id = mlflow.get_experiment_by_name("experiment_name")

with mlflow.start_run(experiment_id=exp_id, run_name=run_name, nested=True):

    study = optuna.create_study(direction="maximize")
    

    study.optimize(objective_rf_acc, n_trials=20, callbacks=[champion_callback])

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

    model = RandomForestClassifier(**study.best_params, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    test_metrics = custom_reports(model, X_test, y_test)
    mlflow.log_metrics(test_metrics)

    artifact_path = "model_rf_acc"

    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path=artifact_path,
        metadata={"model_data_version": 1},
    )

    # Get the logged model uri so that we can load it from the artifact store
    model_uri = mlflow.get_artifact_uri(artifact_path)
```

### Validar que las corridas hayan quedado registradas en MLFlow

Se observan las dos corridas principales, y las 20 corridas anidadas de cada una de estas:

![imagen](images/7-validacion_mlflow.png)

![imagen](images/8-validacion_mlflow_2.png)

También se puede observar que en las principales quedo almacenado el modelo (sin estar registrado aún como modelo).

![imagen](images/9-validacion_mlflow_modelo.png)

### Registro del modelo

Hasta este punto los modelos están en los experimentos pero no hay un modelo registrado. A continuación se abre el modelo y se registra con el nombre `iris_model` y se repite este paso para el otro modelo, pero sin crear un nombre, sino agregandolo al creado.

![imagen](images/10-registro_modelo.png)

Para definir cual será el modelo marcado para procesos de inferencia se usa la herramienta de comparación desplegando solo las métricas distintas:

![imagen](images/11-comparacion_modelos.png)

Se puede observar que el segundo modelo obtuvo una métrica de AUROC ligeramente mejor y que, en las demás métricas de prueba, ambos modelos tienen el mismo desempeño. Debido a este pequeño desempate, se elige el modelo en el que se optimizó la búsqueda según el AUROC.

### Marca de modelo para inferencia

Para esta marca productiva se usa la nueva funcionalidad de aliases, como se osberva en la [documentación](https://www.mlflow.org/docs/latest/model-registry/#migrating-from-stages):

>To replace and improve upon stages, we elevated model version tags in the UI and introduced model version aliases to provide flexible and powerful ways to label and alias MLflow models in the Model Registry. We also made it possible to set up separate environments for your models and configure access controls for each environment.

![imagen](images/12-alias.png)

### Implementación de modelo en API

Se implementa el siguiente código para la carga del modelo:

```python
# Configuración de MLflow
MLFLOW_TRACKING_URI = "http://10.43.101.189:5000"
os.environ['MLFLOW_S3_ENDPOINT_URL'] = "http://10.43.101.189:9000"
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MLFLOW_MODEL_URI = "models:/iris_model@champion"
model = None

def load_model():
    """Carga el modelo desde MLflow si no está disponible"""
    global model
    print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
    if model is None:
        try:
            model = mlflow.pyfunc.load_model(MLFLOW_MODEL_URI)
            print(f"Modelo cargado correctamente desde MLflow: {MLFLOW_MODEL_URI}")
        except mlflow.exceptions.MlflowException as e:
            print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
            print(f"Error de MLflow al cargar el modelo: {e}")
            raise HTTPException(status_code=500, detail=f"Error en MLflow al cargar el modelo.")
```
Y se puede observar por los logs que el modelo está cargando correctamente y se logra predecir la categoría con éxito con docs:

![imagen](images/13-logs_fastapi.png)

![imagen](images/14-predicciones.png)

![imagen](images/15-predicciones.png)