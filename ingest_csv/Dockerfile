FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install requests kafka-python

CMD ["python", "consumer_csv.py"]
