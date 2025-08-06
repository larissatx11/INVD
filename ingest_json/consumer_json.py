import requests
import os
import time
import json
from kafka import KafkaProducer

# === CONFIGURAÇÕES ===
API_URL = "http://api_colmeia:8000/dados"
JSON_PATH = "/app/ingest_json/saida/dados.json"

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def init_json_file():
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w") as f:
            pass

def main():
    init_json_file()

    while True:
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                dado = response.json()
                subset = {
                    "id_colmeia": dado["id_colmeia"],
                    "id": dado["id"],
                    "createdAt": dado["createdAt"],
                    "updatedAt": dado["updatedAt"],
                    "temp": dado["temp"],
                    "humidity": dado["humidity"],
                }

                # Salva localmente
                with open(JSON_PATH, "a") as f:
                    f.write(json.dumps(subset) + "\n")

                print("📄 JSON salvo:", subset)

                # Envia para o Kafka
                producer.send("dados_json", value=subset)
                producer.flush()
                print("🚀 Enviado para Kafka [dados_json]")

            else:
                print(f"❌ Erro na API: {response.status_code}")
        except Exception as e:
            print("❌ Erro geral:", e)

        time.sleep(2)

if __name__ == "__main__":
    main()