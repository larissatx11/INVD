import requests
import csv
import os
import time
import json
from kafka import KafkaProducer
from minio import Minio
from minio.error import S3Error

# === CONFIGURAÇÕES ===
API_URL = "http://api_colmeia:8000/dados"
CSV_PATH = "/app/ingest_csv/saida/saida_csv.csv"
KAFKA_TOPIC = "dados_csv"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"

# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "colmeias-raw"
S3_OBJECT_NAME = "csv/saida_csv.csv"

def init_csv_file():
    if not os.path.isfile(CSV_PATH):
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id_colmeia","id", "createdAt", "updatedAt", "fullWeight", "honeyWeight", "pressure"])

def create_kafka_producer():
    for i in range(10):
        try:
            print(f"[Kafka] Tentando conectar... tentativa {i+1}")
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            print("[Kafka] Conectado ao Kafka!")
            return producer
        except Exception as e:
            print(f"[Kafka] Ainda indisponível: {e}")
            time.sleep(2)
    raise Exception("Kafka indisponível após várias tentativas.")

def upload_to_minio():
    client = Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )
    try:
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)
        client.fput_object(
            bucket_name=BUCKET_NAME,
            object_name=S3_OBJECT_NAME,
            file_path=CSV_PATH,
            content_type="text/csv"
        )
        print(f"[MinIO] CSV enviado para {BUCKET_NAME}/{S3_OBJECT_NAME}")
    except S3Error as e:
        print(f"[MinIO] Erro ao enviar para MinIO: {e}")

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
    producer = None
    tentativas = 0

    while True:
        try:
            if producer is None:
                tentativas += 1
                try:
                    producer = create_kafka_producer()
                except Exception as e:
                    print(f"[Kafka] Erro ao criar producer: {e}")
                    producer = None

            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                dado = response.json()
                subset = {
                    "id_colmeia": dado["id_colmeia"],
                    "id": dado["id"],
                    "createdAt": dado["createdAt"],
                    "updatedAt": dado["updatedAt"],
                    "fullWeight": dado["fullWeight"],
                    "honeyWeight": dado["honeyWeight"],
                    "pressure": dado["pressure"]
                }

                with open(CSV_PATH, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(subset.values())

                if producer:
                    producer.send(KAFKA_TOPIC, value=subset)
                    producer.flush()
                    print(f"[CSV+Kafka] Dados enviados: {subset}")
                else:
                    print(f"[CSV] Kafka off, mas CSV salvo: {subset}")

                upload_to_minio()

            else:
                print(f"Erro na API: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Erro de requisição: {str(e)}")
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")

        time.sleep(2)

if __name__ == "__main__":
    main()
