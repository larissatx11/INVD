FROM python:3.11-slim

WORKDIR /app

COPY . . 

RUN pip install pandas minio

CMD ["python", "transform_csv.py"]
