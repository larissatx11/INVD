import requests
import json
import time

API_URL = "http://api_colmeia:8000/dados"  # nome do serviço no docker-compose

def main():
    while True:
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                dado = response.json()
                subset = {
                    "id": dado["id"],
                    "createdAt": dado["createdAt"],
                    "updatedAt": dado["updatedAt"],
                    "temp": dado["temp"],
                    "humidity": dado["humidity"],
                }
                # Altere a parte de escrita para:
                output_path = "/app/ingest_json/saida/dados.json"  # Caminho absoluto

                with open(output_path, "a") as f:
                    f.write(json.dumps(subset) + "\n")
                    
                print("JSON salvo:", subset)
            else:
                print(f"Erro na API: {response.status_code}")
        except Exception as e:
            print("Erro:", e)
        time.sleep(2)

if __name__ == "__main__":
    main()
