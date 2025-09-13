import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from config import Config

# Настройка страницы
st.set_page_config(
    page_title="Order Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .success { color: #28a745; }
    .warning { color: #ffc107; }
    .danger { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

class Database:
    @staticmethod
    def get_connection():
        try:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            return conn
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None

def get_orders(status_filter=None):
    """Список заказов"""
    conn = Database.get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if status_filter:
                cursor.execute("""
                    SELECT o.*, c.name as customer_name 
                    FROM orders o 
                    JOIN customers c ON o.customer_id = c.id 
                    WHERE o.current_status = %s 
                    ORDER BY o.order_date DESC
                """, (status_filter,))
            else:
                cursor.execute("""
                    SELECT o.*, c.name as customer_name 
                    FROM orders o 
                    JOIN customers c ON o.customer_id = c.id 
                    ORDER BY o.order_date DESC
                """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        return []
    finally:
        conn.close()

def get_order_details(order_id):
    """Детали заказа"""
    conn = Database.get_connection()
    if not conn:
        return None, []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Информация о заказе
            cursor.execute("""
                SELECT o.*, c.name as customer_name, c.address 
                FROM orders o 
                JOIN customers c ON o.customer_id = c.id 
                WHERE o.id = %s
            """, (order_id,))
            order = cursor.fetchone()
            
            # Товары в заказе
            cursor.execute("""
                SELECT oi.*, p.name as product_name 
                FROM order_items oi 
                JOIN products p ON oi.product_id = p.id 
                WHERE oi.order_id = %s
            """, (order_id,))
            items = cursor.fetchall()
            
            return order, items
    except Exception as e:
        st.error(f"Error fetching order details: {e}")
        return None, []
    finally:
        conn.close()

def get_products():
    """Список товаров"""
    conn = Database.get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                ORDER BY p.name
            """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return []
    finally:
        conn.close()

def get_customers():
    """Список клиентов"""
    conn = Database.get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM customers ORDER BY name")
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching customers: {e}")
        return []
    finally:
        conn.close()

def add_product_to_order(order_id, product_id, quantity):
    """Добавление товара в заказ"""
    conn = Database.get_connection()
    if not conn:
        return False, "Database connection error"
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Наличие товара
            cursor.execute("SELECT quantity, price FROM products WHERE id = %s FOR UPDATE", (product_id,))
            product = cursor.fetchone()
            
            if not product:
                return False, "Product not found"
            
            if product['quantity'] < quantity:
                return False, f"Insufficient stock. Available: {product['quantity']}"
            
            # Наличие товара уже в заказе
            cursor.execute("SELECT id, quantity FROM order_items WHERE order_id = %s AND product_id = %s", 
                          (order_id, product_id))
            existing_item = cursor.fetchone()
            
            if existing_item:
                new_quantity = existing_item['quantity'] + quantity
                cursor.execute("UPDATE order_items SET quantity = %s WHERE id = %s", 
                              (new_quantity, existing_item['id']))
            else:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, product_id, quantity, product['price']*quantity))
            
            cursor.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s", 
                          (quantity, product_id))
            
            conn.commit()
            return True, "Product added successfully"
            
    except Exception as e:
        conn.rollback()
        return False, f"Error: {e}"
    finally:
        conn.close()

def create_order(customer_id):
    """Создать новый заказ"""
    conn = Database.get_connection()
    if not conn:
        return None, "Database connection error"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO orders (customer_id, current_status) 
                VALUES (%s, 'new') 
                RETURNING id
            """, (customer_id,))
            order_id = cursor.fetchone()[0]
            conn.commit()
            return order_id, "Order created successfully"
    except Exception as e:
        conn.rollback()
        return None, f"Error: {e}"
    finally:
        conn.close()

def update_order_status(order_id, status):
    """Обновление статуса заказа"""
    conn = Database.get_connection()
    if not conn:
        return False, "Database connection error"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE orders SET current_status = %s WHERE id = %s", (status, order_id))
            conn.commit()
            return True, "Status updated successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_dashboard_stats():
    """Статистика для дашборда"""
    conn = Database.get_connection()
    if not conn:
        return {}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Общая статистика
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(price) as total_revenue,
                    AVG(price) as avg_order_value
                FROM order_items 
            """)
            stats = cursor.fetchone()
            
            # Статистика по статусам
            cursor.execute("""
                SELECT current_status, COUNT(*) as count 
                FROM orders 
                GROUP BY current_status
            """)
            status_stats = cursor.fetchall()
            
            # Топ товаров
            cursor.execute("""
                SELECT p.name, SUM(oi.quantity) as total_sold
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                GROUP BY p.id, p.name
                ORDER BY total_sold DESC
                LIMIT 10
            """)
            top_products = cursor.fetchall()
            
            return {
                'total_orders': stats['total_orders'] or 0,
                'total_revenue': stats['total_revenue'] or 0,
                'avg_order_value': stats['avg_order_value'] or 0,
                'status_stats': status_stats,
                'top_products': top_products
            }
    except Exception as e:
        st.error(f"Error fetching dashboard stats: {e}")
        return {}
    finally:
        conn.close()

# Основное приложение
def main():
    st.markdown('<h1 class="main-header">Order Management System</h1>', unsafe_allow_html=True)
    
    # Сайдбар с навигацией
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Orders", "Add to Order", "Products", "Customers"])
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Orders":
        show_orders()
    elif page == "Add to Order":
        add_to_order()
    elif page == "Products":
        show_products()
    elif page == "Customers":
        show_customers()

def show_dashboard():
    st.header("Dashboard")
    
    stats = get_dashboard_stats()
    
    # Метрики
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Orders", stats.get('total_orders', 0))
    with col2:
        st.metric("Total Revenue", f"{stats.get('total_revenue', 0):.2f} ₽")
    with col3:
        st.metric("Avg Order Value", f"{stats.get('avg_order_value', 0):.2f} ₽")
    
    # График статусов заказов
    if stats.get('status_stats'):
        status_df = pd.DataFrame(stats['status_stats'])
        fig = px.pie(status_df, values='count', names='current_status', title='Order Status Distribution')
        st.plotly_chart(fig)
    
    # Топ товаров
    if stats.get('top_products'):
        st.subheader("Top Selling Products")
        top_df = pd.DataFrame(stats['top_products'])
        fig = px.bar(top_df, x='name', y='total_sold', title='Top 10 Products by Sales')
        st.plotly_chart(fig)

def show_orders():
    st.header("Orders Management")
    
    # Фильтр по статусу
    status_filter = st.selectbox("Filter by status", 
                                ["All", "new", "processing", "shipped", "delivered"])
    
    if status_filter == "All":
        orders = get_orders()
    else:
        orders = get_orders(status_filter)
    
    if orders:
        # Отображение заказов в таблице
        orders_df = pd.DataFrame(orders)
        orders_df['order_date'] = pd.to_datetime(orders_df['order_date']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(orders_df[['id', 'customer_name', 'current_status', 'order_date']])
        
        # Детализация заказа
        selected_order_id = st.selectbox("Select order for details", 
                                        [f"{o['id']} - {o['customer_name']}" for o in orders])
        order_id = int(selected_order_id.split(' - ')[0])
        
        order, items = get_order_details(order_id)
        if order:
            st.subheader(f"Order #{order_id} Details")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Customer:** {order['customer_name']}")
                st.write(f"**Address:** {order['address']}")
                st.write(f"**Status:** {order['current_status']}")
            with col2:
                st.write(f"**Order Date:** {order['order_date'].strftime('%Y-%m-%d %H:%M')}")
            
            # Товары в заказе
            if items:
                st.subheader("Order Items")
                items_df = pd.DataFrame(items)
                items_df['total_price'] = items_df['quantity'] * items_df['price']
                st.dataframe(items_df[['product_name', 'quantity', 'price', 'total_price']])
            
            # Изменение статуса
            new_status = st.selectbox("Change status", 
                                    ["new", "processing", "shipped", "delivered"],
                                    index=["new", "processing", "shipped", "delivered"].index(order['current_status']))
            
            if st.button("Update Status") and new_status != order['current_status']:
                success, message = update_order_status(order_id, new_status)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    else:
        st.info("No orders found")

def add_to_order():
    st.header("Add Product to Order")
    
    # Выбор заказа
    orders = get_orders()
    if not orders:
        st.warning("No orders available. Please create an order first.")
        return
    
    order_options = [f"{o['id']} - {o['customer_name']} ({o['current_status']})" for o in orders]
    selected_order = st.selectbox("Select Order", order_options)
    order_id = int(selected_order.split(' - ')[0])
    
    # Проверка статуса заказа
    order, _ = get_order_details(order_id)
    if order and order['current_status'] not in ['new', 'processing']:
        st.error(f"Cannot add products to order with status: {order['current_status']}")
        return
    
    # Выбор товара
    products = get_products()
    if not products:
        st.warning("No products available.")
        return
    
    product_options = [f"{p['id']} - {p['name']} (Stock: {p['quantity']})" for p in products]
    selected_product = st.selectbox("Select Product", product_options)
    product_id = int(selected_product.split(' - ')[0])
    
    # Получение информации о выбранном товаре
    selected_product_info = next((p for p in products if p['id'] == product_id), None)
    
    if selected_product_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Price:** {selected_product_info['price']:.2f} ₽")
        with col2:
            st.write(f"**Stock:** {selected_product_info['quantity']}")
        with col3:
            st.write(f"**Category:** {selected_product_info['category_name']}")
    
    # Ввод количества
    quantity = st.number_input("Quantity", min_value=1, max_value=selected_product_info['quantity'] if selected_product_info else 100, value=1)
    
    if st.button("Add to Order"):
        if quantity > selected_product_info['quantity']:
            st.error(f"Not enough stock. Available: {selected_product_info['quantity']}")
        else:
            success, message = add_product_to_order(order_id, product_id, quantity)
            if success:
                st.success(message)
            else:
                st.error(message)

def show_products():
    st.header("Products Inventory")
    
    products = get_products()
    if products:
        products_df = pd.DataFrame(products)
        st.dataframe(products_df[['name', 'category_name', 'quantity', 'price']])
        
        # График остатков товаров
        fig = px.bar(products_df, x='name', y='quantity', title='Product Stock Levels')
        st.plotly_chart(fig)
    else:
        st.info("No products found")

def show_customers():
    st.header("Customers")
    
    customers = get_customers()
    if customers:
        customers_df = pd.DataFrame(customers)
        st.dataframe(customers_df)
        
        # Создание нового заказа
        st.subheader("Create New Order")
        selected_customer = st.selectbox("Select Customer", 
                                        [f"{c['id']} - {c['name']}" for c in customers])
        customer_id = int(selected_customer.split(' - ')[0])
        
        if st.button("Create New Order"):
            order_id, message = create_order(customer_id)
            if order_id:
                st.success(f"Order #{order_id} created successfully!")
            else:
                st.error(message)
    else:
        st.info("No customers found")

if __name__ == "__main__":
    main()