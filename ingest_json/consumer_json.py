import requests
import csv
import os
import time
import json
from minio import Minio
from minio.error import S3Error

# === CONFIGURAÇÕES ===
API_URL = "http://api_colmeia:8000/dados"
JSON_PATH = "/app/ingest_json/saida/dados.json"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "colmeias-raw"
S3_OBJECT_NAME = "api/dados.json"  # caminho no bucket

# === Funções ===
def init_json_file():
    """Cria o arquivo JSON vazio, se não existir"""
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w") as f:
            pass  # cria o arquivo vazio

def upload_to_minio():
    """Envia o JSON para o MinIO"""
    client = Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False  # use True se for HTTPS
    )

    try:
        # Cria o bucket se não existir
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)

        # Faz upload do arquivo local para o bucket
        client.fput_object(
            bucket_name=BUCKET_NAME,
            object_name=S3_OBJECT_NAME,
            file_path=JSON_PATH,
            content_type="text/json"
        )
        print(f"JSON enviado para MinIO: {BUCKET_NAME}/{S3_OBJECT_NAME}")
    except S3Error as e:
        print(f"Erro ao enviar para o MinIO: {e}")

# === Loop principal ===
def main():
    init_json_file()

    while True:
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                dado = response.json()
                subset = {
                    "id_colmeia": dado["id_colmeia"],
                    "id": dado["id"],
                    "createdAt": dado["createdAt"],
                    "updatedAt": dado["updatedAt"],
                    "temp": dado["temp"],
                    "humidity": dado["humidity"],
                }

                with open(JSON_PATH, "a") as f:
                    f.write(json.dumps(subset) + "\n")
                
                print("📄 JSON salvo localmente:", subset)

                # Envia para o MinIO
                upload_to_minio()

            else:
                print(f"❌ Erro na API: {response.status_code}")
        except Exception as e:
            print("❌ Erro geral:", e)

        time.sleep(2)

if __name__ == "__main__":
    main()
