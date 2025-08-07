from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'pipeline_monitoramento_colmeias',
    default_args=default_args,
    description='Pipeline completo usando caminhos reais',
    schedule_interval=timedelta(minutes=10),
    start_date=days_ago(1),
    catchup=False,
)

ingest_api = BashOperator(
    task_id='ingestao_api',
    bash_command='python /opt/airflow/ingest/consumer_api.py',
    dag=dag,
)

ingest_db = BashOperator(
    task_id='ingestao_db',
    bash_command='python /opt/airflow/ingest_db/consumer_db.py',
    dag=dag,
)

export_db = BashOperator(
    task_id='exportar_db',
    bash_command='python /opt/airflow/ingest_db/exportador_json.py',
    dag=dag,
)

transform_csv = BashOperator(
    task_id='transformar_csv',
    bash_command='python /opt/airflow/processing_csv/consumer_transform_csv.py',
    dag=dag,
)

transform_json = BashOperator(
    task_id='transformar_json',
    bash_command='python /opt/airflow/processing_json/consumer_transform_json.py',
    dag=dag,
)

carga_dw = BashOperator(
    task_id='carga_dw',
    bash_command='echo "Simulando carga para o Data Warehouse..."',
    dag=dag,
)

[ingest_api, ingest_db] >> export_db >> [transform_csv, transform_json] >> carga_dw
