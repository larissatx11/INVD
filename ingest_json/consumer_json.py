import requests
import os
import time
import json
from kafka import KafkaProducer
from minio import Minio
from minio.error import S3Error
from datetime import datetime

# === CONFIGURAÇÕES ===
API_URL = "http://api_colmeia:8000/dados"
JSON_DIR = "/app/ingest_json/saida"
MINIO_BUCKET = "colmeias-raw"
KAFKA_TOPIC = "novo_dado_raw"

# Kafka
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# MinIO
minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def wait_for_minio(max_attempts=10, delay=3):
    for attempt in range(1, max_attempts + 1):
        try:
            # Tenta listar buckets como teste de conexão
            minio_client.list_buckets()
            print("✅ MinIO está pronto!")
            return
        except Exception as e:
            print(f"⏳ Aguardando MinIO... Tentativa {attempt}/{max_attempts}")
            time.sleep(delay)
    raise Exception("❌ MinIO não ficou pronto após várias tentativas.")

def init_setup():
    os.makedirs(JSON_DIR, exist_ok=True)
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)

def salvar_localmente(dado):
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    filename = f"dado_{timestamp}.json"
    full_path = os.path.join(JSON_DIR, filename)

    with open(full_path, "w") as f:
        json.dump(dado, f)

    return filename, full_path

def enviar_para_minio(nome, caminho):
    try:
        minio_client.fput_object(
            MINIO_BUCKET,
            f"api/{nome}",
            caminho,
            content_type="application/json"
        )
        print(f"✅ JSON enviado para MinIO: api/{nome}")
    except S3Error as e:
        print("❌ Erro MinIO:", e)

def main():
    wait_for_minio()
    init_setup()

    while True:
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                dado = response.json()
                filename, path = salvar_localmente(dado)
                enviar_para_minio(filename, path)

                # Publica no Kafka o nome do arquivo
                producer.send(KAFKA_TOPIC, value={"filename": filename})
                producer.flush()
                print("🚀 Publicado no Kafka:", filename)
            else:
                print(f"❌ Erro na API: {response.status_code}")
        except Exception as e:
            print("❌ Erro geral:", e)

        time.sleep(2)

if __name__ == "__main__":
    main()