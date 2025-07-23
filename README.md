para rodar todo o projeto:

sudo docker-compose up --build



para ver as atualizações no BD:

watch -n 2 "sudo docker exec -i trabalho_final_mysql_1 mysql -u root -proot -e 'USE colmeia; SELECT * FROM dados_colmeia ORDER BY registro DESC LIMIT 5;'"