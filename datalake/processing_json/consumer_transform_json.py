import os
import json
import time
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from minio import Minio
from minio.error import S3Error

# Config
KAFKA_TOPIC = "novo_dado_raw"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
RAW_BUCKET = "colmeias-raw"
PROC_BUCKET = "colmeias-processing"
MINIO_ENDPOINT = "minio:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"

OUTPUT_DIR = "/app/processing_json/saida"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Kafka
for _ in range(10):
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        break
    except NoBrokersAvailable:
        print("Kafka não disponível, tentando novamente em 5s...")
        time.sleep(5)
else:
    raise Exception("Kafka não disponível após várias tentativas")

# MinIO
client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False
)

def wait_for_minio(max_attempts=10, delay=3):
    for attempt in range(1, max_attempts + 1):
        try:
            # Tenta listar buckets como teste de conexão
            client.list_buckets()
            print(" MinIO está pronto!")
            return
        except Exception as e:
            print(f" Aguardando MinIO... Tentativa {attempt}/{max_attempts}")
            time.sleep(delay)
    raise Exception(" MinIO não ficou pronto após várias tentativas.")


def transformar(dado):
    try:
        dado["umidade_ideal"] = float(dado["humidity"]) > 50
        temp = float(dado["temp"])
        dado["alerta_calor"] = temp > 36 or temp < 34
        return dado
    except Exception as e:
        print(" Erro ao transformar:", e)
        return None

def processar_arquivo(filename):
    # Baixa o arquivo do MinIO (raw)
    if filename.endswith('.json'):
        objeto = f"api/{filename}"
        local_path = os.path.join(OUTPUT_DIR, f"raw_{filename}")
        try:
            client.fget_object(RAW_BUCKET, objeto, local_path)
        except Exception as e:
            print(f" Erro ao baixar {objeto} do MinIO:", e)
            return

    with open(local_path, "r") as f:
        dado = json.load(f)

    transformado = transformar(dado)
    if not transformado:
        return

    # Salva localmente
    output_file = os.path.join(OUTPUT_DIR, f"transf_{filename}")
    with open(output_file, "w") as f:
        json.dump(transformado, f)

    # Envia para MinIO (processing)
    try:
        client.fput_object(
            PROC_BUCKET,
            f"json/{filename}",
            output_file,
            content_type="application/json"
        )
        print(f" Transformado e enviado para MinIO: json/{filename}")
    except S3Error as e:
        print(" Erro no upload para processing:", e)

def main():
    wait_for_minio()
    if not client.bucket_exists(PROC_BUCKET):
        client.make_bucket(PROC_BUCKET)

    for msg in consumer:
        filename = msg.value.get("filename")
        if filename.endswith(".json"):
            print(" Novo arquivo detectado:", filename)
            processar_arquivo(filename)
        else:
            print(f" Ignorando arquivo não JSON: {filename}")

if __name__ == "__main__":
    main()
