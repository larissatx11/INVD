import mysql.connector
import json
import os
import time
from datetime import datetime, timedelta

ARQUIVO_EXPORTADO = os.path.join("saida", "dados_exportados.json")
ARQUIVO_TIMESTAMP = os.path.join("saida", "ultimo_exportado.txt")

def create_connection():
    return mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="colmeia",
        auth_plugin='mysql_native_password'
    )

def ler_ultimo_timestamp():
    if not os.path.exists(ARQUIVO_TIMESTAMP):
        return "1970-01-01 00:00:00"
    with open(ARQUIVO_TIMESTAMP, "r") as f:
        return f.read().strip()

def salvar_ultimo_timestamp(timestamp):
    with open(ARQUIVO_TIMESTAMP, "w") as f:
        f.write(timestamp)

def exportar_dados():
    ultimo_ts = ler_ultimo_timestamp()

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    os.makedirs("saida", exist_ok=True)

    try:
        # Usar > em vez de >= para evitar pegar o último registro novamente
        cursor.execute("""
            SELECT * FROM dados_colmeia
            WHERE registro > %s
            ORDER BY registro ASC, id ASC
        """, (ultimo_ts,))
        dados = cursor.fetchall()

        if not dados:
            print("⚠️ Nenhum novo dado para exportar.")
            return

        # Modo write ('w') em vez de append para recriar o arquivo cada vez
        with open(ARQUIVO_EXPORTADO, "w", encoding="utf-8") as f:
            for dado in dados:
                for campo in ["created_at", "updated_at", "registro"]:
                    if dado[campo] and isinstance(dado[campo], datetime):
                        dado[campo] = dado[campo].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                json.dump(dado, f, ensure_ascii=False)
                f.write("\n")

        # Usar o registro mais recente como novo ponto de partida
        ultimo_registro = dados[-1]["registro"]
        salvar_ultimo_timestamp(ultimo_registro.strftime("%Y-%m-%d %H:%M:%S.%f"))

        print(f"📤 Exportados {len(dados)} novos dados.")

    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
    finally:
        if conn.is_connected():
            conn.close()

def main():
    while True:
        exportar_dados()
        time.sleep(10)

if __name__ == "__main__":
    main()