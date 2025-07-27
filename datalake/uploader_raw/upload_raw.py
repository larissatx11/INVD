import os
import time
from minio import Minio
from minio.error import S3Error
from datetime import datetime

# Configurações do MinIO
endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")

bucket_name = "colmeias-raw"
subpastas = {
    "api": "/app/ingest_json/saida",
    "csv": "/app/ingest_csv/saida",
    "db-dump": "/app/ingest_db/saida"
}

# Aguarda o MinIO estar pronto
for i in range(10):
    try:
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        if client.bucket_exists(bucket_name):
            break
    except Exception as e:
        print(f"Tentativa {i+1}/10 falhou: {e}")
        time.sleep(10)

# Cria bucket se não existir
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)
    print(f"Bucket '{bucket_name}' criado.")
else:
    print(f"Bucket '{bucket_name}' já existe.")

# Faz upload de cada tipo de dado
for subpasta, local_path in subpastas.items():
    for file in os.listdir(local_path):
        full_path = os.path.join(local_path, file)
        if os.path.isfile(full_path):
            nome_objeto = f"{subpasta}/{file}"
            try:
                client.fput_object(bucket_name, nome_objeto, full_path)
                print(f"Enviado: {nome_objeto}")
            except S3Error as err:
                print(f"Erro ao enviar {file}: {err}")