import json
import os
import pandas as pd
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error

KAFKA_TOPIC = "dados_csv"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"

OUTPUT_PATH = "/app/processing_csv/saida/saida_csv_tratado.csv"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "colmeias-processing"
S3_OBJECT_NAME = "csv/saida_csv_tratado.csv"

historico = []

def transformar_linha(linha):
    global historico
    historico.append(linha)

    if len(historico) > 3:
        historico.pop(0)

    try:
        linha["fullWeight"] = float(linha["fullWeight"])
        linha["honeyWeight"] = float(linha["honeyWeight"])
        linha["pressure"] = float(linha["pressure"])
    except Exception as e:
        print("[Erro conversão]", e)
        return None

    if len(historico) > 1:
        linha["variacao_peso"] = linha["fullWeight"] - historico[-2]["fullWeight"]
    else:
        linha["variacao_peso"] = 0

    if len(historico) == 3:
        linha["necessidade_alimentacao"] = all(float(h["honeyWeight"]) == 0 for h in historico)
    else:
        linha["necessidade_alimentacao"] = False

    linha["pressao_anomala"] = not (980 <= linha["pressure"] <= 1030)

    return linha

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
            content_type="text/csv"
        )
        print(f"[MinIO] Enviado para {BUCKET_NAME}/{S3_OBJECT_NAME}")
    except S3Error as e:
        print("[MinIO ERRO]:", e)

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset='latest',
        enable_auto_commit=True
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    if not os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "w") as f:
            f.write("id_colmeia,id,createdAt,updatedAt,fullWeight,honeyWeight,pressure,variacao_peso,necessidade_alimentacao,pressao_anomala\n")

    for msg in consumer:
        linha = msg.value
        linha_transformada = transformar_linha(linha)

        if linha_transformada:
            df = pd.DataFrame([linha_transformada])
            df.to_csv(OUTPUT_PATH, mode='a', header=False, index=False)
            print("[Transformado] Nova linha salva e transformada:", linha_transformada)
            upload_para_minio()

if __name__ == "__main__":
    main()
