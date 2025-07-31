import pandas as pd
import os
from minio import Minio
from minio.error import S3Error

INPUT_PATH = "/app/entrada_csv/saida_csv.csv"
OUTPUT_PATH = "/app/saida_csv/saida_csv_tratado.csv"

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "colmeias-processing"
S3_OBJECT_NAME = "csv/saida_csv_tratado.csv"

def transformar_csv(df):
    df["fullWeight"] = pd.to_numeric(df["fullWeight"], errors="coerce")
    df["honeyWeight"] = pd.to_numeric(df["honeyWeight"], errors="coerce")
    df["pressure"] = pd.to_numeric(df["pressure"], errors="coerce")

    df["variacao_peso"] = df["fullWeight"].diff()
    df["necessidade_alimentacao"] = df["honeyWeight"].rolling(3).apply(lambda x: all(i == 0 for i in x)).fillna(0).astype(bool)
    df["pressao_anomala"] = ~df["pressure"].between(980, 1030)

    return df

def upload_to_minio():
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
    print(f"[MinIO] CSV enriquecido enviado para {BUCKET_NAME}/{S3_OBJECT_NAME}")

def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"[ERRO] Arquivo {INPUT_PATH} não encontrado.")
        return

    df = pd.read_csv(INPUT_PATH)
    df = transformar_csv(df)
    df.to_csv(OUTPUT_PATH, index=False)
    print("[Transformação] CSV transformado salvo em:", OUTPUT_PATH)

    upload_to_minio()

if __name__ == "__main__":
    main()
