FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install minio requests
RUN pip install requests kafka-python minio

CMD ["python", "consumer_csv.py"]
