FROM python:3.11-slim

WORKDIR /app

COPY upload_raw.py .
RUN pip install minio

CMD ["python", "upload_raw.py"]