FROM python:3.10
WORKDIR /app
COPY consumer_db.py /app/
RUN pip install requests mysql-connector-python minio
CMD ["python", "consumer_db.py"]