import requests
import csv
import os
import time
import json
from kafka import KafkaProducer

API_URL = "http://api_colmeia:8000/dados"
CSV_PATH = "/app/ingest_csv/saida/saida_csv.csv"
KAFKA_TOPIC = "dados_csv"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092" 

def init_csv_file():
    if not os.path.isfile(CSV_PATH):
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "createdAt", "updatedAt", "fullWeight", "honeyWeight", "pressure"])

def create_kafka_producer():
    for i in range(10):  
        try:
            print(f"[Kafka] Tentando conectar... tentativa {i+1}")
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            print("[Kafka] Conectado com sucesso!")
            return producer
        except Exception as e:
            print(f"[Kafka] Kafka ainda indisponível: {e}")
            time.sleep(2)
    raise Exception("Kafka indisponível após várias tentativas.")

def main():
    init_csv_file()
    producer = None  
    tentativas = 0

    while True:
        try:
            
            if producer is None:
                tentativas += 1
                print(f"[Kafka] Tentando conectar... tentativa {tentativas}")
                try:
                    producer = create_kafka_producer()
                    print("[Kafka] Conectado ao Kafka com sucesso!")
                except Exception as e:
                    print(f"[Kafka] Kafka ainda indisponível: {e}")
                    producer = None 

            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                dado = response.json()
                subset = {
                    "id": dado["id"],
                    "createdAt": dado["createdAt"],
                    "updatedAt": dado["updatedAt"],
                    "fullWeight": dado["fullWeight"],
                    "honeyWeight": dado["honeyWeight"],
                    "pressure": dado["pressure"]
                }

                with open(CSV_PATH, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(subset.values())

                if producer:
                    producer.send(KAFKA_TOPIC, value=subset)
                    producer.flush()
                    print(f"[CSV+Kafka] Dados salvos + enviados: {subset}")
                else:
                    print(f"[CSV] Dados salvos localmente (Kafka indisponível): {subset}")
            else:
                print(f"Erro na API: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {str(e)}")
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")

        time.sleep(2)

if __name__ == "__main__":
    main()
