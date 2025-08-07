import os
import json
import time
import pandas as pd
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

OUTPUT_DIR = "/app/processing_csv/saida"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Kafka
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
            client.list_buckets()
            print(" MinIO está pronto!")
            return
        except Exception as e:
            print(f" Aguardando MinIO... Tentativa {attempt}/{max_attempts}")
            time.sleep(delay)
    raise Exception(" MinIO não ficou pronto após várias tentativas.")

def transformar_csv(dado, historico):
    try:
        dado["fullWeight"] = float(dado["fullWeight"])
        dado["honeyWeight"] = float(dado["honeyWeight"])
        dado["pressure"] = float(dado["pressure"])
    except Exception as e:
        print("[Erro conversão]", e)
        return None

    historico.append(dado)
    if len(historico) > 3:
        historico.pop(0)

    if len(historico) > 1:
        dado["variacao_peso"] = dado["fullWeight"] - historico[-2]["fullWeight"]
    else:
        dado["variacao_peso"] = 0

    if len(historico) == 3:
        dado["necessidade_alimentacao"] = all(float(h["honeyWeight"]) == 0 for h in historico)
    else:
        dado["necessidade_alimentacao"] = False

    dado["pressao_anomala"] = not (980 <= dado["pressure"] <= 1030)

    return dado

def processar_arquivo(filename, historico):
    # Baixa o arquivo do MinIO (raw)
    if filename.endswith('.csv'):
        objeto = f"csv/{filename}"
        local_path = os.path.join(OUTPUT_DIR, f"raw_{filename}")
        try:
            client.fget_object(RAW_BUCKET, objeto, local_path)
        except Exception as e:
            print(f" Erro ao baixar {objeto} do MinIO:", e)
            return

    # Lê o CSV e transforma
    try:
        df = pd.read_csv(local_path)
        linhas_transformadas = []
        for _, row in df.iterrows():
            linha = row.to_dict()
            linha_tratada = transformar_csv(linha, historico)
            if linha_tratada:
                linhas_transformadas.append(linha_tratada)
    except Exception as e:
        print(" Erro ao processar CSV:", e)
        return

    if not linhas_transformadas:
        return

    # Salva localmente
    output_file = os.path.join(OUTPUT_DIR, f"transf_{filename}")
    df_out = pd.DataFrame(linhas_transformadas)
    df_out.to_csv(output_file, index=False)

    # Envia para MinIO (processing)
    try:
        client.fput_object(
            PROC_BUCKET,
            f"csv/{filename}",
            output_file,
            content_type="text/csv"
        )
        print(f" Transformado e enviado para MinIO: csv/{filename}")
    except S3Error as e:
        print(" Erro no upload para processing:", e)

def main():
    wait_for_minio()
    if not client.bucket_exists(PROC_BUCKET):
        client.make_bucket(PROC_BUCKET)

    historico = []
    for msg in consumer:
        filename = msg.value.get("filename")
        if filename.endswith('.csv'):
            print(" Novo arquivo detectado:", filename)
            processar_arquivo(filename, historico)
        else:
            print(f" Ignorando arquivo não CSV: {filename}")

if __name__ == "__main__":
    main()