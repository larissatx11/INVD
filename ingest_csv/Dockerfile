FROM python:3.10

WORKDIR /app

COPY consumer_csv.py /app/
RUN pip install requests

CMD ["python", "consumer_csv.py"]
