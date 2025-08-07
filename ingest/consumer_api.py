import requests
import json
import csv
import os
import time
from datetime import datetime
from minio import Minio
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import mysql.connector  # ADICIONADO

# === CONFIGURAÇÕES ===
API_URL = "http://api_colmeia:8000/dados"

# Caminhos locais
JSON_DIR = "/app/ingest/json/"
CSV_DIR = "/app/ingest/csv/"
BD_JSON_DIR = "/app/ingest/bd_json/"  # NOVO: json transformado vindo do banco

# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BUCKET_NAME = "colmeias-raw"

# Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = "novo_dado_raw"

# MySQL
MYSQL_CONFIG = {
    "host": "mysql",
    "user": "colmeia_user",
    "password": "colmeia_pass",
    "database": "colmeia",
}

# Criação dos diretórios
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(BD_JSON_DIR, exist_ok=True)

# MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False,
)

def wait_for_minio(max_attempts=10, delay=3):
    for attempt in range(1, max_attempts + 1):
        try:
            minio_client.list_buckets()
            print("✅ MinIO está pronto!")
            if not minio_client.bucket_exists(BUCKET_NAME):
                minio_client.make_bucket(BUCKET_NAME)
            return
        except Exception:
            print(f"⏳ Aguardando MinIO... Tentativa {attempt}/{max_attempts}")
            time.sleep(delay)
    raise Exception("❌ MinIO não ficou pronto após várias tentativas.")

# Kafka
for _ in range(10):
    try:
        producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
        break
    except NoBrokersAvailable:
        print("Kafka não disponível, tentando novamente em 5s...")
        time.sleep(5)
else:
    raise Exception("Kafka não disponível após várias tentativas")

# === BANCO DE DADOS ===

def create_table_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dados_colmeia (
            id VARCHAR(255) PRIMARY KEY,
            id_colmeia INT,
            created_at DATETIME,
            updated_at DATETIME,
            temp FLOAT,
            humidity FLOAT,
            full_weight FLOAT,
            honey_weight FLOAT,
            pressure FLOAT,
            battery FLOAT,
            is_open BOOLEAN,
            registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def salvar_no_banco(dado):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    create_table_if_not_exists(conn)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dados_colmeia (
            id, id_colmeia, created_at, updated_at,
            temp, humidity, full_weight, honey_weight,
            pressure, battery, is_open
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            updated_at=VALUES(updated_at),
            temp=VALUES(temp),
            humidity=VALUES(humidity),
            full_weight=VALUES(full_weight),
            honey_weight=VALUES(honey_weight),
            pressure=VALUES(pressure),
            battery=VALUES(battery),
            is_open=VALUES(is_open)
    """, (
        dado["id"],
        dado["id_colmeia"],
        datetime.strptime(dado["createdAt"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f"),
        datetime.strptime(dado["updatedAt"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f"),
        float(dado["temp"]),
        float(dado["humidity"]),
        float(dado["fullWeight"]),
        float(dado["honeyWeight"]),
        float(dado["pressure"]),
        float(dado["battery"]),
        dado["isOpen"]
    ))

    conn.commit()
    cursor.close()
    conn.close()


def recuperar_dado_do_banco(id_dado):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM dados_colmeia WHERE id = %s", (id_dado,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

# === FUNÇÕES DE SALVAMENTO LOCAL E ENVIO ===

def salvar_json_local(dado, nome_arquivo, dir_path=JSON_DIR):
    caminho = os.path.join(dir_path, nome_arquivo)
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

# ... (seu código acima permanece igual até aqui) ...

def map_dado_bd_para_formato_api(dado_bd):
    if not dado_bd:
        return None
    return {
        "id": dado_bd.get("id"),
        "id_colmeia": dado_bd.get("id_colmeia"),
        "createdAt": dado_bd.get("created_at").strftime("%Y-%m-%dT%H:%M:%S.%fZ") if dado_bd.get("created_at") else None,
        "updatedAt": dado_bd.get("updated_at").strftime("%Y-%m-%dT%H:%M:%S.%fZ") if dado_bd.get("updated_at") else None,
        "temp": str(dado_bd.get("temp")),
        "humidity": str(dado_bd.get("humidity")),
        "fullWeight": str(dado_bd.get("full_weight")),
        "honeyWeight": str(dado_bd.get("honey_weight")),
        "pressure": str(dado_bd.get("pressure")),
        "battery": str(dado_bd.get("battery")),
        "isOpen": dado_bd.get("is_open"),
    }

def main():
    wait_for_minio()

    while True:
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                dado = response.json()

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_base = f"dado_{timestamp}.json"
                nome_csv = nome_base.replace(".json", ".csv")
                nome_bdjson = nome_base.replace(".json", "_frombd.json")

                # Salvar JSON e CSV originais localmente
                json_path = salvar_json_local(dado, nome_base)
                csv_path = salvar_csv_local(dado, nome_csv)

                # Salvar no banco
                salvar_no_banco(dado)

                # Recuperar do banco
                dado_bd = recuperar_dado_do_banco(dado["id"])
                dado_bd_formatado = map_dado_bd_para_formato_api(dado_bd)

                if dado_bd_formatado:
                    # Salvar JSON transformado localmente
                    bdjson_path = salvar_json_local(dado_bd_formatado, nome_bdjson, BD_JSON_DIR)

                    # Enviar arquivos para MinIO
                    enviar_para_minio(json_path, "api")
                    enviar_para_minio(csv_path, "csv")
                    enviar_para_minio(bdjson_path, "bd")

                    # Publicar no Kafka após envio dos 3 arquivos
                    publicar_kafka(os.path.basename(json_path), "json")
                    publicar_kafka(os.path.basename(csv_path), "csv")
                    publicar_kafka(os.path.basename(bdjson_path), "bd-json")
                else:
                    print("⚠️ Dado recuperado do banco está vazio ou inválido.")

            else:
                print(f"Erro ao consultar API: {response.status_code}")
        except Exception as e:
            print(f"Erro geral: {e}")

        time.sleep(5)

if __name__ == "__main__":
    main()
