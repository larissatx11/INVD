FROM python:3.11-slim

WORKDIR /app

COPY consumer_transform_kafka.py .

RUN pip install kafka-python pandas minio

CMD ["python", "consumer_transform_kafka.py"]
