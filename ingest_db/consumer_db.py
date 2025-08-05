import requests
import mysql.connector
import time
from datetime import datetime
API_URL = "http://api_colmeia:8000/dados"

def create_connection():
    return mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="colmeia",
        auth_plugin='mysql_native_password'
    )

def ensure_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dados_colmeia (
        id_colmeia INT NOT NULL,
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
    return datetime.strptime(dt_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S.%f")

def insert_or_update_data(conn, data):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO dados_colmeia 
        (id_colmeia, id, created_at, updated_at, battery, is_open)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            updated_at = VALUES(updated_at),
            battery = VALUES(battery),
            is_open = VALUES(is_open)
        """, (
            data["id_colmeia"],
            data["id"],
            parse_datetime(data["createdAt"]),
            parse_datetime(data["updatedAt"]),
            data["battery"],
            data["isOpen"]
        ))
        conn.commit()
        print(f"✅ Inserido: {data['id']}")
    except Exception as e:
        print(f"❌ Erro ao inserir: {e}")

def main():
    while True:
        try:
            conn = create_connection()
            ensure_table_exists(conn)

            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                insert_or_update_data(conn, response.json())
            else:
                print(f"❌ Erro API: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro geral: {e}")
        finally:
            if conn.is_connected():
                conn.close()
        time.sleep(1)

if __name__ == "__main__":
    main()
