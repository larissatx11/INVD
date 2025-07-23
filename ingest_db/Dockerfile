FROM python:3.8-slim
WORKDIR /app
COPY consumer_db.py .
RUN pip install requests mysql-connector-python
CMD ["python", "consumer_db.py"]