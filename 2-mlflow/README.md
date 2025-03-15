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

```
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