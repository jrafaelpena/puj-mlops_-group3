FROM python:3.11-slim

WORKDIR /locust

COPY locustfile.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8089

CMD ["locust", "-f", "locustfile.py"]