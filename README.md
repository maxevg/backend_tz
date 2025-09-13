# Структура проекта

* app.py - файл с реализованным RestApi функционалом сервиса
* streamlit_app.py - файл c веб функционалом для добавление и изменение заказов
* database.py - вспомогательный файл для работы с бд
* config.py - конфигурационный файл впоследствии можно добавить .env
* init.sql - файл для инициализации бд
* sql_queries.sql - файл содержит необходимые по тз запросы
* README.md - README пректа

# Запуск сервиса
Достаточно скопировать репозиоторий и в данной директории запустить:
```
docker-compose up 
```
Сервисы:
* localhost:8501 - находится дашборд Streamlit  
* localhost:5000 - Flask RESTApi
* localhost:5432 - Postgresql 

Запросы к app.py:
1) Статус сервера:
```
curl -X GET http://localhost:5000/health
```
2) Добавление товара в заказ
```
curl -X POST http://localhost:5000/api/orders/add-item -H "Content-Type: application/json" -d "{\"order_id\": 2, \"product_id\": 4, \"quantity\": 1}"
```