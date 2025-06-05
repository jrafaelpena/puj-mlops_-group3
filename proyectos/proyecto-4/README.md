# Proyecto 4 MLOps

### [🎥 Ver video en YouTube](https://youtu.be/CgQ7kvihTHg)

Este repositorio contiene todos los artefactos, configuraciones y manifiestos necesarios para construir, desplegar y operar un pipeline completo de Machine Learning orientado a MLOps. A continuación encontrarás:

<br>

## Descripción

El objetivo de este taller es desplegar un pipeline de MLOps que cubra todo el ciclo de vida de un modelo de Machine Learning, desde la ingesta de datos brutos hasta la entrega de resultados de inferencia a través de una API y una interfaz web.

<br>

## Componentes principales

1. **Airflow**: Orquesta la recolección, preprocesamiento y entrenamiento continuo de un modelo.
2. **MLflow**: Registra experimentos, métricas e historial de modelos.
3. **Bases de datos (PostgreSQL/MySQL)**: Almacenan datos RAW, datos limpios y metadatos para MLflow.
4. **MinIO**: Bucket que actúa como sistema de archivos para artefactos (modelos, reportes, logs).
5. **FastAPI (Inference API)**: Expone un endpoint REST para recibir solicitudes de inferencia usando el último modelo en producción.
6. **Streamlit (UI de inferencia)**: Interfaz web que permite al usuario final interactuar con el modelo, visualizar resultados y explorar versiones históricas.
7. **Prometheus & Grafana**: Capturan métricas de latencia y tráfico de la API para análisis en tiempo real.
8. **Locust**: Herramienta de pruebas de carga para evaluar el rendimiento de la Inference API.
9. **Argo CD**: GitOps para mantener todos los manifiestos de Kubernetes sincronizados y facilitar despliegues declarativos.

Todo lo anterior se ejecuta sobre un clúster Kubernetes (MicroK8s, EKS, GKE, etc.) y se basa en manifiestos organizados en carpetas “base/” y “overlays/” para facilitar la reutilización.

<br>

## Diagrama de arquitectura del proyect

<img src="images/project.jpg" width="95%">

<br>

## Estructura del repositorio

    ├── .argocd-apps/
    │   ├── airflow-app.yaml
    │   ├── inference-api-app.yaml
    │   ├── streamlit-app.yaml
    │   └── apps-of-apps.yaml
    │
    ├── apps/
    │   ├── airflow/
    │   │   ├── dags/
    │   │   │   ├── project-pipeline.py
    │   │   │   ├── raw_data_creation.sq
    │   │   │   └── utils.py
    │   │   └── image/
    │   │       ├── Dockerfile
    │   │       ├── pyproject.toml
    │   │       └── README.md
    │   │
    │   ├── inference-api/
    │   │   ├── Dockerfile
    │   │   ├── pyproject.toml
    │   │   ├── .python-version
    │   │   └── app/
    │   │       └── main.py
    │   │
    │   ├── streamlit/
    │   │   ├── Dockerfile
    │   │   ├── pyproject.toml
    │   │   ├── .python-version
    │   │   └── streamlit_app.py
    │   │
    │   └── locust/
    │       └── locustfile.py
    │
    ├── charts/
    │   └── airflow/
    │       └── Chart.yaml
    │
    ├── images/
    │   ├── arquitectura_proyecto.png
    │   ├── dag_flow.png
    │   └── ...
    │
    ├── k8s/
    │   ├── base/
    │   │   └── namespace.yaml
    │   │
    │   ├── airflow/
    │   │   └── values.yaml
    │   │
    │   ├── inference-api/
    │   │   ├── kustomization.yaml
    │   │   └── inference-api.yaml
    │   │
    │   ├── mlflow/
    │   │   ├── kustomization.yaml
    │   │   ├── mysql.yaml
    │   │   ├── mysql-pvc.yaml
    │   │   ├── minio.yaml
    │   │   ├── minio-pv.yaml
    │   │   └── mlflow.yaml
    │   │
    │   ├── observability/
    │   │   ├── kustomization.yaml
    │   │   ├── prometheus.yaml
    │   │   ├── grafana.yaml
    │   │   └── grafana-dashboard-config.yam
    │   │
    │   ├── postgres/
    │   │   ├── kustomization.yaml
    │   │   ├── postgres.yaml
    │   │   └── postgres-pvc.yaml
    │   │
    │   ├── pvs/
    │   │   ├── kustomization.yaml
    │   │   ├── minio-pv.yaml
    │   │   ├── mysql-pv.yaml
    │   │   └── postgres-pv.yaml
    │   │
    │   └── streamlit/
    │       ├── kustomization.yaml
    │       └── streamlit.yaml
    │
    ├── .argocd-apps/
    │   ├── airflow-app.yaml
    │   ├── inference-api-app.yaml
    │   ├── streamlit-app.yaml
    │   └── apps-of-apps.yaml
    │
    ├── Makefile / deploy.sh
    ├── README.md
    └── LICENSE

<br>

## Desarrollo

### 1. Creación automática del bucket Minio

Al desplegar MLflow en Kubernetes, necesitamos asegurarnos de que existan dos buckets en Minio para almacenar artefactos y datos relacionados:

- mlflows3
- api-artifacts

En lugar de crear manualmente estos buckets después de levantar Minio, se configuran _init containers_ dentro del Deployment de MLflow para:
- Esperar a que Minio esté listo.
- Crear (si no existen) los buckets necesarios.

De esta forma, cada vez que MLflow se inicie (o se redeploye), se garantiza que los buckets estén presentes, evitando errores de artefactos faltantes en tiempo de ejecución.

<br>


### 2. Grafana

ConfigMaps usados para provisionar automáticamente Grafana en Kubernetes: definir la fuente de datos (Prometheus), configurar el proveedor de dashboards (dashboard provider) y cargar el dashboard en sí (JSON).

**grafana-datasource**

- Este ConfigMap define la(s) fuente(s) de datos (datasource) que Grafana debe registrar al iniciar. En este caso, se le está indicando que agregue Prometheus como datasource por defecto, apuntando al servicio http://prometheus:9090. Grafana leerá automáticamente el contenido de datasource.yaml en /etc/grafana/provisioning/datasources/. Al levantar el pod de Grafana, encontrará el datasource “Prometheus” configurado, sin necesidad de hacerlo manualmente vía UI. Gracias a la clave isDefault: true, cualquier panel nuevo utilizará a Prometheus como fuente de métricas.


**grafana-dashboard-provider**

- Define la forma en que Grafana debe buscar archivos JSON de dashboards dentro del contenedor. Es el “dashboard provider” que apunta a un directorio local (/var/lib/grafana/dashboards). Se crea un ConfigMap que Grafana montará en /etc/grafana/provisioning/dashboards/provider.yaml. Grafana escaneará cada updateIntervalSeconds (10 s) la ruta /var/lib/grafana/dashboards en busca de archivos JSON. Al encontrar grafana-dashboard.json (u otros JSON), los cargará como dashboards “provisionados” en la organización (orgId = 1), sin permitir su eliminación desde la interfaz (disableDeletion: false significa que sí se pueden eliminar, pero suelen llenarse/reescribirse desde este provider). allowUiUpdates: true permite editarlo desde la UI, aunque cualquier cambio local puede perderse en el próximo reinicio si se sobrescribe el ConfigMap.

**rafana-dashboard-config**

- Contiene el JSON completo del dashboard que se desea provisionar en Grafana. El label grafana_dashboard: "1" hace que, al montar el ConfigMap en el directorio de dashboards, Grafana lo reconozca y lo cargue automáticamente. Grafana monta este ConfigMap (por ejemplo, bajo /var/lib/grafana/dashboards/grafana-dashboard.json). Gracias al “dashboard provider” configurado en grafana-dashboard-provider.yaml, Grafana detecta este archivo JSON y lo importa como un dashboard nuevo llamado “Tablero Proyecto 4”. Este JSON define: Paneles, fuentes de datos, métricas, expresiones PromQL (por ejemplo, rate(http_requests_total[5m])), disposición (gridPos), opciones de estilo (dark), intervalos de refresco (10 s), etc. Cada vez que se actualice este ConfigMap a nivel de Kubernetes, Grafana sobrescribirá el dashboard con la nueva versión del JSON.
<br>


### 3. Dag

Este DAG está diseñado para operar de manera completamente automática. Se encarga de procesar por lotes (batch) los datos de precios de casas, realizando tareas de carga, limpieza, entrenamiento y evaluación de modelos.

El pipeline incluye dos mecanismos clave:

    AirflowSkipException
    
En la primera tarea (evaluate_run_and_load_raw_data), si la API de datos indica que no hay más lotes disponibles (o retorna un error HTTP), se lanza esta excepción. Esto detiene el DAG sin marcarlo como fallido, evitando así ejecuciones innecesarias y previendo loops infinitos.

    TriggerDagRunOperator
    
Cuando todas las tareas se ejecutan correctamente, esta operación dispara automáticamente una nueva ejecución del mismo DAG para procesar el siguiente lote. Así se logra una secuencia encadenada de ejecuciones sin intervención manual.

Este mecanismo permite que el pipeline:
- Se reinicie automáticamente cuando se procesó un lote exitosamente.
- Se detenga de forma segura cuando ya no hay más datos por procesar.

El pipeline es completamente autónomo, procesando cada lote de datos de forma escalonada hasta agotar la fuente sin necesidad de loops explícitos.

<br>


### 4. Pipeline

El flujo de entrenamiento está diseñado con una lógica robusta de control de versiones de modelos y comparación de desempeño utilizando MLflow.

**Funciones principales**

    evaluate_run_and_load_raw_data:
Obtiene el lote desde una API externa y lo almacena en la base de datos.

    preprocess_and_split:
Limpia los datos, crea bins de precios para estratificación y separa en conjuntos de entrenamiento y prueba.

    train_decesision:
Evalúa si el tamaño del nuevo lote justifica reentrenar el modelo (se entrena si el 60% o más de los datos son nuevos).

    train_model:
Entrena el modelo con LinearRegression y OneHotEncoder, evalúa el desempeño con custom_reports_regression y lo registra en MLflow.

**Lógica de "Champion" y "Challenger"**

El pipeline implementa una lógica de control de versiones y evaluación progresiva:

- El primer modelo (lote 0) se registra automáticamente como champion.

- Los modelos entrenados en lotes posteriores se registran como challenger.

- Se comparan las métricas de evaluación, especialmente el RMSE.

- Si el modelo challenger tiene mejor o igual RMSE que el actual champion, entonces:

- Se actualiza el alias champion en MLflow.

- Se llama a la API de inferencia para cargar el nuevo modelo.

Esta arquitectura permite que solo los mejores modelos pasen a producción, garantizando mejoras continuas en el sistema sin necesidad de supervisión manual.


<br>


### 5. Github Actions

**Workflows**

*1. project-4.yaml*
   
Automáticamente reconstruye y publica imágenes Docker para los componentes inference-api y streamlit del proyecto proyecto-4.

- Se ejecuta manualmente desde GitHub (workflow_dispatch).
- Clona el código del repo

- Hace login a Docker Hub usando secretos

- Publica las imágenes en Docker Hub

- Construye dos imágenes con docker buildx:

        jrpenagu/fastapi-house-prices

        jrpenagu/streamlit-house-prices

- Etiqueta las imágenes con:

        :latest

        El SHA corto del commit (ej. :e4a1c9)

<br>

Este workflow se activa cuando se hace push a la rama main y hay cambios en:

- apps/inference-api/**

- apps/streamlit/**


<br>


*2. ci-cd.yml*
   
Ejecuta un flujo CI más especializado para la API de inferencia (fast-api-iris) de un taller, incluyendo instalación de dependencias, entrenamiento y publicación de modelo.

- Se ejecuta con push a main en:

    4/taller-ci-cd/api-inferencia/**

    4/taller-ci-cd/params.yaml
    También admite ejecución manual.

- Clona el código

- Instala dependencias con uv (gestor de entornos)

- Configura Python según .python-version

- Entrena un modelo ejecutando train_model.py

- Publica el modelo entrenado como artefacto de GitHub Actions
- A diferencia del primer workflow, este no construye imágenes Docker, sino que automatiza el flujo de ML con instalación, entrenamiento y almacenamiento del modelo.


El flujo principal (project-4.yaml) garantiza que los contenedores de producción siempre estén actualizados cuando se modifican sus scripts o dependencias. Por su parte, el segundo workflow (ci-cd.yml) permite gestionar el ciclo de vida del modelo de ML, facilitando el entrenamiento reproducible y la publicación.

<br>

## Conclusiones

Este taller ofrece una guía completa y práctica para desplegar un pipeline de MLOps moderno, completamente automatizado, modular y desplegable en Kubernetes. A lo largo del desarrollo, se integran múltiples tecnologías que permiten cubrir todo el ciclo de vida de un modelo de machine learning:
- Orquestación de procesamiento y entrenamiento por lotes con Airflow, incluyendo mecanismos automáticos de parada (AirflowSkipException) y reinicio (TriggerDagRunOperator), garantizando un flujo autónomo sin loops infinitos.
- Registro de experimentos y control de versiones con MLflow, respaldado por almacenamiento en MinIO y metadatos en MySQL, lo cual permite comparar métricas y realizar despliegue controlado mediante el esquema champion/challenger.
- Despliegue de modelos mediante un servicio de inferencia REST (FastAPI), con recarga automática del modelo cuando un nuevo challenger supera al champion.
- Visualización de resultados y métricas con Streamlit, ofreciendo una interfaz ligera e interactiva para explorar los datos y predicciones.
- Monitoreo de métricas en tiempo real con Prometheus y Grafana, incluyendo dashboards provisionados automáticamente desde Kubernetes mediante ConfigMaps.
- Automatización del entrenamiento y despliegue con GitHub Actions, a través de dos workflows:

    - project-4.yaml: detecta cambios en los scripts y dependencias de inference-api y streamlit, construye las imágenes Docker, las etiqueta y publica automáticamente en Docker Hub.

    - ci-cd.yml: gestiona el ciclo de vida del modelo ML para una API de inferencia, ejecutando instalación, entrenamiento y publicación del modelo como artefacto.
      
- Infraestructura definida como código mediante manifiestos YAML y Kustomize, desplegada y sincronizada con Argo CD, asegurando consistencia entre versiones y facilidad de rollback o actualización.
