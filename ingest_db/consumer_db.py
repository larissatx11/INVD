import requests
import mysql.connector
import time
import os
from datetime import datetime

API_URL = "http://api_colmeia:8000/dados"

def create_connection():
    try:
        conn = mysql.connector.connect(
            host="mysql",
            user="root",
            password="root",
            database="colmeia",
            auth_plugin='mysql_native_password'
        )
        print("✅ Conexão com MySQL estabelecida!")
        return conn
    except Exception as e:
        print(f"❌ Falha na conexão: {str(e)}")
        raise

def ensure_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dados_colmeia (
        id VARCHAR(255) PRIMARY KEY,
        created_at DATETIME,
        updated_at DATETIME,
        battery FLOAT,
        is_open BOOLEAN,
        registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

def parse_datetime(dt_str):
    """
    Converte data no formato ISO 8601 com 'T' e 'Z' para formato MySQL
    """
    try:
        # Remove o 'Z' e converte para datetime
        dt = datetime.strptime(dt_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S.%f")
        # Retorna string no formato aceito pelo MySQL
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except Exception as e:
        print(f"Erro ao converter data: {dt_str} | {str(e)}")
        return None

def insert_or_update_data(conn, data):
    cursor = conn.cursor()
    try:
        created_at = parse_datetime(data["createdAt"])
        updated_at = parse_datetime(data["updatedAt"])
        
        cursor.execute("""
        INSERT INTO dados_colmeia 
        (id, created_at, updated_at, battery, is_open)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            updated_at = VALUES(updated_at),
            battery = VALUES(battery),
            is_open = VALUES(is_open)
        """, (
            data["id"],
            created_at,
            updated_at,
            data["battery"],
            bool(data["isOpen"])
        ))
        conn.commit()
        print(f"✅ Dados persistidos no BD: {data['id']}")
    except Exception as e:
        print(f"❌ Erro ao persistir dados: {str(e)}")

def main():
    time.sleep(15)  # Espera o MySQL inicializar
    
    while True:
        conn = None
        try:
            conn = create_connection()
            ensure_table_exists(conn)
            
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                insert_or_update_data(conn, response.json())
            else:
                print(f"❌ Erro na API (HTTP {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Falha na requisição: {str(e)}")
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
        finally:
            if conn and conn.is_connected():
                conn.close()
                
        time.sleep(2)

if __name__ == "__main__":
    main()
