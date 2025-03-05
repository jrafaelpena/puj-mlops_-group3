# MLOps - Desarrollo de Pipeline Automatizado

Este proyecto está orientado a la implementación de un flujo de trabajo automatizado para el desarrollo, validación y despliegue de modelos de Machine Learning. Se busca establecer un entorno reproducible y escalable que facilite la experimentación y producción de modelos, minimizando los errores manuales y asegurando la trazabilidad de los datos y modelos en cada etapa.

El enfoque principal es la construcción de una canalización robusta que permita:

- *Ingesta y procesamiento de datos:* Preparación del dataset, validación y detección de anomalías.
- *Versionamiento y monitoreo:* Gestión estructurada del código, datos y modelos con herramientas de control de versiones.
- *Automatización del ciclo de vida del modelo:* Uso de pipelines para transformar, entrenar y evaluar modelos de manera eficiente.
- *Despliegue en entornos aislados:* Configuración basada en contenedores para garantizar portabilidad y escalabilidad.

## Requisitos

Este proyecto requiere las siguientes tecnologías para su ejecución:

- *Docker & Docker Compose* para la gestión de entornos aislados.
- *Python 3.8+* con dependencias definidas en requirements.txt.
- *Jupyter Notebook* para el desarrollo y documentación del flujo de trabajo.
- *Git & GitHub* para la gestión del código y colaboración en equipo.

## Instalación

Para desplegar este entorno, se deben seguir los siguientes pasos:

1. Clonar el repositorio:
   sh
   git clone https://github.com/usuario/repositorio.git
   cd repositorio
   
2. Construir y desplegar los contenedores de infraestructura:
   sh
   docker-compose up --build
   
3. Ejecutar el entorno interactivo con Jupyter Notebook:
   sh
   jupyter notebook
   

## Estructura del Repositorio

La estructura del proyecto está organizada de la siguiente manera:


📂 proyecto-1/
 ├── data/covertype/     # Conjunto de datos utilizado en el proyecto
 ├── pipeline/           # Implementación del pipeline de procesamiento
 ├── .python-version     # Versión de Python utilizada
 ├── Dockerfile.jupyter  # Configuración del entorno en Docker
 ├── README.md           # Documentación del proyecto
 ├── docker-compose.yml  # Configuración de Docker Compose
 ├── notebook.ipynb      # Implementación y ejecución de pruebas en Jupyter
 ├── pyproject.toml      # Configuración del entorno de desarrollo
 ├── uv.lock             # Archivos de bloqueo para dependencias


## Flujo de Trabajo

1. *Carga y Preprocesamiento de Datos*
   - Ingesta de datos desde fuentes externas.
   - Validación de la estructura y calidad del conjunto de datos.
   - Transformaciones necesarias para la preparación del modelo.

2. *Desarrollo del Pipeline de Datos*
   - Configuración de un flujo estructurado de procesamiento.
   - Aplicación de esquemas personalizados para validación y monitoreo.
   - Versionamiento de los artefactos generados.

3. *Gestión de Modelos y Versionamiento*
   - Control de versiones en GitHub para asegurar la trazabilidad.
   - Gestión de metadatos para auditoría y replicabilidad.
   - Implementación de estrategias de actualización y despliegue de modelos.

## Contacto y Soporte

Para dudas o sugerencias, se puede abrir un issue en GitHub o contribuir a la discusión en la comunidad del proyecto.
