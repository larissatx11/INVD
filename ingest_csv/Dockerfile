FROM python:3.11-slim

WORKDIR /app

COPY consumer_csv.py /app/
RUN pip install minio requests
COPY . .

RUN pip install requests kafka-python minio

CMD ["python", "consumer_csv.py"]
