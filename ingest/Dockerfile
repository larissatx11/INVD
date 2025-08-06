FROM python:3.11-slim

WORKDIR /app

COPY consumer_api.py .

RUN pip install kafka-python minio mysql-connector-python requests

CMD ["python", "consumer_api.py"]
