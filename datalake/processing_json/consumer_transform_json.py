import os
import json
import time
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error

KAFKA_TOPIC = "dados_json"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
OUTPUT_PATH = "/app/processing_json/saida/saida_json_tratado.json"
BUCKET_NAME = "colmeias-processing"
S3_OBJECT_NAME = "json/saida_json_tratado.json"

# MinIO config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

def transformar(dado):
    try:
        dado["umidade_ideal"] = float(dado["humidity"]) > 50
        temp = float(dado["temp"])
        dado["alerta_calor"] = temp > 36 or temp < 34
        return dado
    except Exception as e:
        print("❌ Erro ao transformar:", e)
        return None

def upload_para_minio():
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            secure=False
        )

        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)

        client.fput_object(
            bucket_name=BUCKET_NAME,
            object_name=S3_OBJECT_NAME,
            file_path=OUTPUT_PATH,
            content_type="application/json"
        )
        print(f"✅ JSON transformado enviado ao MinIO em {BUCKET_NAME}/{S3_OBJECT_NAME}")
    except S3Error as e:
        print("❌ Erro MinIO:", e)

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset='latest',
        enable_auto_commit=True
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    open(OUTPUT_PATH, "a").close()  # cria o arquivo vazio se não existir

    for msg in consumer:
        dado = msg.value
        transformado = transformar(dado)

        if transformado:
            with open(OUTPUT_PATH, "a") as f:
                f.write(json.dumps(transformado) + "\n")
            print("📝 Dado transformado salvo:", transformado)
            upload_para_minio()

if __name__ == "__main__":
    main()