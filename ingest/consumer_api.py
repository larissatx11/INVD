import requests
import json
import csv
import os
import time
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# === CONFIGURAÇÕES ===
API_URL = "http://api_colmeia:8000/dados"

# Caminhos locais
JSON_DIR = "/app/ingest/json/"
CSV_DIR = "/app/ingest/csv/"

# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BUCKET_NAME = "colmeias-raw"

# Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = "novo_dado_raw"

# Criação dos diretórios, se não existirem
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

# Conecta ao MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False,
)

def wait_for_minio(max_attempts=10, delay=3):
    for attempt in range(1, max_attempts + 1):
        try:
            # Tenta listar buckets como teste de conexão
            minio_client.list_buckets()
            print("✅ MinIO está pronto!")
            # Cria o bucket se ele não existir
            if not minio_client.bucket_exists(BUCKET_NAME):
                minio_client.make_bucket(BUCKET_NAME)
            return
        except Exception as e:
            print(f"⏳ Aguardando MinIO... Tentativa {attempt}/{max_attempts}")
            time.sleep(delay)
    raise Exception("❌ MinIO não ficou pronto após várias tentativas.")

# Conecta ao Kafka
for _ in range(10):
    try:
        producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
        break
    except NoBrokersAvailable:
        print("Kafka não disponível, tentando novamente em 5s...")
        time.sleep(5)
else:
    raise Exception("Kafka não disponível após várias tentativas")

def salvar_json_local(dado, nome_arquivo):
    caminho = os.path.join(JSON_DIR, nome_arquivo)
    with open(caminho, "w") as f:
        json.dump(dado, f, indent=4)
    return caminho

def salvar_csv_local(dado, nome_arquivo):
    caminho = os.path.join(CSV_DIR, nome_arquivo)
    with open(caminho, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=dado.keys())
        writer.writeheader()
        writer.writerow(dado)
    return caminho

def enviar_para_minio(caminho_arquivo_local, pasta_destino_minio):
    nome_arquivo = os.path.basename(caminho_arquivo_local)
    destino = f"{pasta_destino_minio}/{nome_arquivo}"
    minio_client.fput_object(BUCKET_NAME, destino, caminho_arquivo_local)
    print(f"✔ Enviado ao MinIO: {BUCKET_NAME}/{destino}")

def publicar_kafka(nome_arquivo, tipo):
    payload = {
        "filename": nome_arquivo,
        "tipo": tipo
    }
    producer.send(KAFKA_TOPIC, json.dumps(payload).encode("utf-8"))
    print(f"✔ Publicado no Kafka: {KAFKA_TOPIC} - {payload}")

def main():
    wait_for_minio()
    
    while True:
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                dado = response.json()

                # Gera nome com timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_base = f"dado_{timestamp}.json"
                nome_csv = nome_base.replace(".json", ".csv")

                # Salvar local
                json_path = salvar_json_local(dado, nome_base)
                csv_path = salvar_csv_local(dado, nome_csv)

                # Enviar para MinIO
                enviar_para_minio(json_path, "api")
                enviar_para_minio(csv_path, "csv")

                # Publicar no Kafka o nome do arquivo JSON
                publicar_kafka(os.path.basename(json_path), "json")
                # Publicar no Kafka o nome do arquivo CSV
                publicar_kafka(os.path.basename(csv_path), "csv")

            else:
                print(f"Erro ao consultar API: {response.status_code}")
        except Exception as e:
            print(f"Erro geral: {e}")

        time.sleep(5)

if __name__ == "__main__":
    main()
