# Taller Locust

## Estructura del proyecto




Es muy importante aclarar que el taller se desarrolla teniendo levantados todos los servicios y la infraestructura (volúmenes manejados, red, entre otros) del proyecto 2. De esta manera, ya sabremos que los servicios de `minio` y `mlflow` están funcionando de manera correcta, y que la imagen para crear el contenedor de inferencia existe y funciona adecuadamente. 

A continuación, se observan los servicios del proyecto 2, y se puede notar que la imagen del servicio `inference-api` es `fast-api-mlflow`:


<img src="images/servicios.png" width="60%">

## Paso 1. Publicar la imagen `fast-api-mlflow` en DockerHub

Antes de subir la imagen a DockerHub, se debe iniciar sesión. En nuestro caso, usamos `docker login` y realizamos el procedimiento con el browser.

Teniendo la imagen `fast-api-mlflow` con la etiqueta `latest`, se deben ejecutar los siguientes comandos para etiquetar la imagen para DockerHub (modificar el repositorio y la etiqueta según corresponda) y hacer push de la imagen:

```bash
docker tag fast-api-mlflow:latest jrpenagu/fast-api-mlflow:latest
docker push jrpenagu/fast-api-mlflow:latest
```

Se obtiene una confirmación de la publicación por consola y se verifica que la imagen se encuentre disponible en DockerHub:

<img src="images/push.png" width="40%">

<img src="images/dockerhub.png" width="40%">

## Paso 2. Despliegue de API y Locust

Se genera un archivo `docker-compose` para dos servicios: el API de inferencia y el servicio de `locust`. Ambos se incluyen en la red ya creada del proyecto 2. A continuación, se muestra cómo se vería el archivo inicialmente (sin réplicas ni configuración de recursos mínimos):

```yaml
services:
  api:
    image: jrpenagu/fast-api-mlflow:latest
    container_name: api-inferencia
    command: uv run uvicorn main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          memory: 500G
          cpus: 0.5
    networks:
      - proyecto-2_default
    restart: "no"

  locust:
    build:
      context: ./locust
    container_name: locust
    ports:
      - "8089:8089"
    depends_on:
      - api
    environment:
      - LOCUST_HOST=http://api:8000
    networks:
      - proyecto-2_default
    restart: "no"

networks:
  proyecto-2_default:
    external: true
```

Inicialmente, se despliegan ambos servicios limitando el API de inferencia a solo 500 MB de memoria y 0.5 CPUs. Sin embargo, esta configuración no es suficiente para soportar la carga del modelo. Incluso al realizar una petición manual, el contenedor falla con código 137 o el mensaje Terminado por SIGKILL (señal 9). Esto generalmente indica que el sistema operativo finalizó el contenedor por falta de memoria (OOM, Out Of Memory).

<img src="images/error.png" width="40%">

Se aumenta la cantidad de memoria con pasos de 100M y se llega a la conclusión que se requieren aproximadamente 1.3 GB para que la API funcione de base.

## Paso 3. Pruebas para recursos mínimos con 10,000 usuarios

Inicialmente, se trabajó con los recursos base y se generó un bloqueo de la máquina virtual (VM), posiblemente debido a la alta cantidad de peticiones enviadas por `locust` sin interrupción. Se apagó la VM y se procedió a asignar un *runtime* máximo de 150 segundos para las pruebas con `locust`, de modo que se detuvieran automáticamente.

Debido al bloqueo, se optó por comenzar con pocos usuarios e ir incrementando gradualmente, tomando decisiones basadas en el monitoreo de los recursos consumidos por el contenedor mediante `docker stats`.

El resumen de estas pruebas se puede encontrar en la siguiente tabla:

<img src="images/tabla_pruebas.png" width="60%">

Para garantizar que estos fueron los recursos mínimos encontrados, se soportan las cifras con capturas de pantalla tanto de las estadísticas de docker como de locust:

<img src="images/final-10000.png" width="60%">

<img src="images/final-10000-locustui.png" width="60%">


