FROM python:3.9-slim

WORKDIR /app

# Instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY streamlit_app.py .

EXPOSE 8503

# Ejecuta la aplicación en el puerto 8503 sin CORS habilitado
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8503", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"]
