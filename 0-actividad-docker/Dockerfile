FROM python:3.10.16

WORKDIR /app


COPY requirements.txt .
COPY main.py .
COPY joblibs/ joblibs/

RUN pip install --no-cache-dir -r requirements.txt


# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8989"]