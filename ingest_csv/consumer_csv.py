import requests
import csv
import os
import time

API_URL = "http://api_colmeia:8000/dados"
CSV_PATH = "/app/ingest_csv/saida/saida_csv.csv"  # Caminho no container

def init_csv_file():
    """Cria o arquivo CSV com cabeçalho se não existir"""
    if not os.path.isfile(CSV_PATH):
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "createdAt", "updatedAt", 
                           "fullWeight", "honeyWeight", "pressure"])

def main():
    init_csv_file()
    
    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                dado = response.json()
                subset = [
                    dado["id"],
                    dado["createdAt"],
                    dado["updatedAt"],
                    dado["fullWeight"],
                    dado["honeyWeight"],
                    dado["pressure"]
                ]
                
                with open(CSV_PATH, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(subset)
                
                print(f"Dados salvos em {CSV_PATH}: {subset}")
            else:
                print(f"Erro na API: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {str(e)}")
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")
            
        time.sleep(2)

if __name__ == "__main__":
    main()