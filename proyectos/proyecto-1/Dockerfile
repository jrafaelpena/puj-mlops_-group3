# No se descarga una imagen de Python, puesto que uv hará todo el trabajo
FROM alpine:latest 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /project-1

# Crear las carpetas necesarias
RUN mkdir -p pipeline data/covertype

COPY pyproject.toml .
COPY uv.lock .
COPY .python-version .
COPY notebook.ipynb .


# Expose port 8888
EXPOSE 8888

# Comando por defecto al iniciar el contenedor
CMD ["uv", "run", "--with", "jupyter", "jupyter", "lab"]


