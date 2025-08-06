import os
import json
import time
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from minio import Minio
from minio.error import S3Error

# Configurações
KAFKA_TOPIC = "novo_dado_raw"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
RAW_BUCKET = "colmeias-raw"
PROC_BUCKET = "colmeias-processing"
MINIO_ENDPOINT = "minio:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"

OUTPUT_DIR = "/app/processing_bd/saida"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Inicializa Kafka consumer
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

# Inicializa MinIO client
client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False
)

def wait_for_minio(max_attempts=10, delay=3):
    for attempt in range(1, max_attempts + 1):
        try:
            client.list_buckets()
            print("✅ MinIO está pronto!")
            return
        except Exception as e:
            print(f"⏳ Aguardando MinIO... Tentativa {attempt}/{max_attempts}")
            time.sleep(delay)
    raise Exception("❌ MinIO não ficou pronto após várias tentativas.")

def transformar_battery_status(dado):
    try:
        battery = float(dado.get("battery", 0))
        if battery < 80:
            dado["battery_status"] = "battery_below_80"
        else:
            dado["battery_status"] = battery
    except Exception as e:
        print(f"[Erro conversão battery_status]: {e}")
        dado["battery_status"] = None
    return dado

def processar_arquivo(filename):
    if not filename.endswith('_frombd.json'):
        print(f"⚠ Ignorando arquivo que não é JSON bd: {filename}")
        return
    
    objeto = f"bd/{filename}"
    local_path = os.path.join(OUTPUT_DIR, f"raw_{filename}")
    
    try:
        client.fget_object(RAW_BUCKET, objeto, local_path)
    except Exception as e:
        print(f"❌ Erro ao baixar {objeto} do MinIO:", e)
        return

    try:
        with open(local_path, 'r') as f:
            dado = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler JSON local {local_path}:", e)
        return

    dado_tratado = transformar_battery_status(dado)
    
    output_file = os.path.join(OUTPUT_DIR, f"transf_{filename}")
    try:
        with open(output_file, 'w') as f:
            json.dump(dado_tratado, f, indent=4)
    except Exception as e:
        print(f"❌ Erro ao salvar JSON transformado {output_file}:", e)
        return
    
    try:
        client.fput_object(
            PROC_BUCKET,
            f"bd/{filename}",
            output_file,
            content_type="application/json"
        )
        print(f"✅ Transformado e enviado para MinIO: bd/{filename}")
    except S3Error as e:
        print("❌ Erro no upload para processing:", e)

def main():
    wait_for_minio()
    if not client.bucket_exists(PROC_BUCKET):
        client.make_bucket(PROC_BUCKET)

    for msg in consumer:
        filename = msg.value.get("filename")
        if filename and filename.endswith('_frombd.json'):
            print("📦 Novo arquivo bd detectado:", filename)
            processar_arquivo(filename)
        else:
            print(f"⚠ Ignorando arquivo não bd_json: {filename}")

if __name__ == "__main__":
    main()
