FROM apache/airflow:2.10.5

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

RUN mkdir -p /tmp/build

COPY pyproject.toml /tmp/build/pyproject.toml

USER root
RUN cd /tmp/build && uv pip install --system --python=/home/airflow/.local/bin/python .

USER airflow
