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