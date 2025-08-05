FROM python:3.10

WORKDIR /app

# Copia todos os scripts (consumer_db.py, exportador_json.py, etc)
COPY . /app/

# Instala dependências
RUN pip install requests mysql-connector-python

# Entrada padrão — espera script via command no compose
ENTRYPOINT ["python"]
