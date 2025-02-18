### Actividad # 2: Taller entrenamiento en Jupyter y consumo de modelos por API usando uv como administrador de paquetes

En la carpeta app se encuentra todo el código necesario para la ejecución del taller.

El archivo `docker-compose.yml` define dos servicios: uno para Jupyter y otro para FastAPI, cada uno utilizando su respectiva imagen. Ambos servicios comparten un volumen llamado `artifacts`, donde se almacenan los modelos entrenados en Jupyter para que la API pueda consumirlos.

Se utiliza uv como gestor de paquetes, instalándolo desde su imagen oficial con el siguiente comando, según la documentación de la librería: `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/`

Para permitir que el usuario entrene modelos y los utilice de inmediato en la API, se implementaron dos métodos GET adicionales:

- `reload_models`: Carga los modelos entrenados para que estén disponibles en la aplicación.
- `available_models`: Devuelve una lista de los modelos disponibles, incluyendo la clave con la que pueden ser referenciados en las solicitudes (`predict_specific_model`), así como información sobre el tipo de modelo (clase de la instancia).
