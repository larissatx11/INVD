import requests
import time
import csv
import os
from kafka import KafkaProducer
import json

API_URL = "http://api_colmeia:8000/dados"
CSV_PATH = "/app/ingest_csv/saida/saida_csv.csv"

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def salvar_em_csv(dado):
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=dado.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(dado)

while True:
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            dado = response.json()
            salvar_em_csv(dado)
            print("[CSV] Dado salvo:", dado)
            producer.send("dados_csv", value=dado)
            producer.flush()
            print("[Kafka] Dado enviado ao tópico")
        else:
            print("Erro ao obter dado:", response.status_code)
    except Exception as e:
        print("Erro:", e)

    time.sleep(2)
