FROM python:3.10

WORKDIR /app

COPY consumer_json.py /app/
RUN pip install minio kafka-python requests

CMD ["python", "consumer_json.py"]
