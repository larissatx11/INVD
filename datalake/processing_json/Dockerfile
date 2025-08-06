FROM python:3.11-slim

WORKDIR /app

COPY consumer_transform_json.py .

RUN pip install kafka-python minio

CMD ["python", "consumer_transform_json.py"]
