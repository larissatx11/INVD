FROM python:3.10

WORKDIR /app

COPY consumer_api.py /app/
RUN pip install minio kafka-python requests

CMD ["python", "consumer_api.py"]
