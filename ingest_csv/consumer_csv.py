import requests
import csv
import os
import time
from minio import Minio
from minio.error import S3Error

# === CONFIGURAÇÕES ===
API_URL = "http://api_colmeia:8000/dados"
CSV_PATH = "/app/ingest_csv/saida/saida_csv.csv"  # local
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "colmeias-raw"
S3_OBJECT_NAME = "csv/saida_csv.csv"  # caminho dentro do bucket

# === Funções ===
def init_csv_file():
    """Cria o arquivo CSV com cabeçalho se não existir"""
    if not os.path.isfile(CSV_PATH):
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "createdAt", "updatedAt", 
                             "fullWeight", "honeyWeight", "pressure"])

def upload_to_minio():
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
            file_path=CSV_PATH,
            content_type="text/csv"
        )
        print(f"CSV enviado para MinIO: {BUCKET_NAME}/{S3_OBJECT_NAME}")
    except S3Error as e:
        print(f"Erro ao enviar para o MinIO: {e}")

def main():
    init_csv_file()

    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                dado = response.json()
                subset = [
                    dado["id"],
                    dado["createdAt"],
                    dado["updatedAt"],
                    dado["fullWeight"],
                    dado["honeyWeight"],
                    dado["pressure"]
                ]
                with open(CSV_PATH, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(subset)
                print(f"Dados salvos localmente: {subset}")

                # Após salvar, envia para o MinIO
                upload_to_minio()
            else:
                print(f"Erro na API: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {str(e)}")
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")

        time.sleep(2)

if __name__ == "__main__":
    main()