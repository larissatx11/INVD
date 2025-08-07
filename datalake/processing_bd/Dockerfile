# Use uma imagem oficial do Python como base
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do seu projeto para dentro do container
COPY . /app

# Instala as dependências necessárias
RUN pip install --no-cache-dir kafka-python minio pandas

# Comando padrão para executar seu consumer (vai ser sobrescrito pelo docker-compose)
CMD ["python3", "consumer_transform_bd.py"]
