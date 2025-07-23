# Monitoramento Apiário Crateús

Este projeto simula o monitoramento de um apiário, enviando dados de sensores (temperatura, umidade, etc.) por meio de uma API. Os dados são consumidos por três fontes de ingestão diferentes: CSV, JSON e banco de dados. O objetivo é demonstrar um pipeline completo de ingestão, processamento e visualização de dados em ambiente Docker.

## Estrutura do Projeto

- **api_simulador/**: Simulador da API que envia dados históricos do apiário.  
- **ingest_csv/**: Serviço que consome dados da API e salva em arquivo CSV.  
- **ingest_json/**: Serviço que consome dados da API e salva em arquivo JSON.  
- **ingest_db/**: Serviço que consome dados da API e insere em banco de dados.  
- **dashboard/**: Dashboard para visualização dos dados ingeridos.  
- **airflow/**: Orquestrador de pipelines (opcional).  
- **docker-compose.yml**: Orquestra todos os serviços em containers.  

## Como executar

Para rodar todo o projeto:

```bash
sudo docker-compose up --build

```
## Visualizando os dados no banco

Para acompanhar as atualizações no banco de dados a cada 2 segundos, utilize:

```bash
watch -n 2 "sudo docker exec -i trabalho_final_mysql_1 mysql -u root -proot -e 'USE colmeia; SELECT * FROM dados_colmeia ORDER BY registro DESC LIMIT 5;'"
