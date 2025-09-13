from flask import Flask, jsonify, request
from flask_restful import Api, Resource
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from database import Database
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
api = Api(app)

class AddToOrderService(Resource):
    def post(self):
        """
        Добавление товара в заказ
        Пример JSON тела запроса:
        {
            "order_id": 2,
            "product_id": 3,
            "quantity": 1
        }
        """
        conn = None
        cursor = None
        
        try:
            data = request.get_json()
            
            # Валидация входных данных
            if not data:
                return {'error': 'No JSON data provided'}, 400
            
            required_fields = ['order_id', 'product_id', 'quantity']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            order_id = data['order_id']
            product_id = data['product_id']
            quantity = data['quantity']
            
            # Проверка валидности quantity
            if not isinstance(quantity, int) or quantity <= 0:
                return {'error': 'Quantity must be a positive integer'}, 400
            
            # Получаем соединение с базой данных
            conn = Database.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Начинаем транзакцию
            conn.autocommit = False
            
            try:
                # 1. Проверяем существование заказа и его статус
                cursor.execute("""
                    SELECT id, current_status FROM orders 
                    WHERE id = %s FOR UPDATE
                """, (order_id,))
                order = cursor.fetchone()
                
                if not order:
                    return {'error': 'Order not found'}, 404
                
                if order['current_status'] not in ['new', 'processing']:
                    return {'error': 'Cannot modify order in current status'}, 400
                
                # 2. Проверяем наличие товара на складе
                cursor.execute("""
                    SELECT id, name, quantity as stock_quantity, price 
                    FROM products 
                    WHERE id = %s FOR UPDATE
                """, (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    return {'error': 'Product not found'}, 404
                
                if product['stock_quantity'] < quantity:
                    return {
                        'error': 'Insufficient stock',
                        'available_quantity': product['stock_quantity'],
                        'requested_quantity': quantity
                    }, 400
                
                # 3. Проверяем, есть ли уже этот товар в заказе
                cursor.execute("""
                    SELECT id, quantity, price 
                    FROM order_items 
                    WHERE order_id = %s AND product_id = %s
                    FOR UPDATE
                """, (order_id, product_id))
                existing_item = cursor.fetchone()
                
                if existing_item:
                    # 4. Если товар уже есть в заказе - обновляем количество
                    new_quantity = existing_item['quantity'] + quantity
                    
                    # Проверяем, не превысит ли это общее количество доступного товара
                    if product['stock_quantity'] < new_quantity:
                        return {
                            'error': 'Insufficient stock for updated quantity',
                            'available_quantity': product['stock_quantity'],
                            'current_in_order': existing_item['quantity'],
                            'requested_additional': quantity
                        }, 400
                    
                    cursor.execute("""
                        UPDATE order_items 
                        SET quantity = %s 
                        WHERE id = %s
                    """, (new_quantity, existing_item['id']))
                    
                    action = 'updated'
                    final_quantity = new_quantity
                    
                else:
                    # 5. Если товара нет в заказе - добавляем новую позицию
                    cursor.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, price)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (order_id, product_id, quantity, product['price']))
                    
                    action = 'added'
                    final_quantity = quantity
                
                # 6. Уменьшаем количество товара на складе
                cursor.execute("""
                    UPDATE products 
                    SET quantity = quantity - %s 
                    WHERE id = %s
                """, (quantity, product_id))
                
                # Коммитим транзакцию
                conn.commit()
                
                return {
                    'message': f'Product {action} to order successfully',
                    'order_id': order_id,
                    'product_id': product_id,
                    'final_quantity': final_quantity,
                    'product_name': product['name'],
                    'price_per_unit': float(product['price'])
                }, 200
                
            except psycopg2.Error as e:
                # Откатываем транзакцию в случае ошибки
                if conn:
                    conn.rollback()
                app.logger.error(f"Database error: {e}")
                return {'error': 'Database operation failed'}, 500
                
            finally:
                if cursor:
                    cursor.close()
                
        except psycopg2.Error as e:
            app.logger.error(f"PostgreSQL error: {e}")
            return {'error': 'Database connection failed'}, 500
        
        except Exception as e:
            app.logger.error(f"Unexpected error: {e}")
            return {'error': 'Internal server error'}, 500
        
        finally:
            if conn:
                Database.return_connection(conn)

# endpoints для мониторинга
class HealthCheck(Resource):
    def get(self):
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            Database.return_connection(conn)
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500

api.add_resource(AddToOrderService, '/api/orders/add-item')
api.add_resource(HealthCheck, '/health')

@app.teardown_appcontext
def close_db_connection(exception=None):
    Database.close_pool()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)