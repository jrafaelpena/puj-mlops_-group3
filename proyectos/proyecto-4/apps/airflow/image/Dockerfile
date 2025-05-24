FROM apache/airflow:2.10.5

RUN mkdir -p /tmp/build

COPY pyproject.toml /tmp/build/pyproject.toml

RUN cd /tmp/build && uv pip install --system --python=/home/airflow/.local/bin/python .