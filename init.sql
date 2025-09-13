-- 1.2 Таблица категорий
CREATE TABLE categories (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- 1.1 Номенклатура
CREATE TABLE products (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL,
    category_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- 1.3 Таблица клиентов
CREATE TABLE customers (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL
);

-- 1.4 Таблица заказов
CREATE TYPE status AS ENUM ('new', 'processing', 'shipped', 'delivered');

CREATE TABLE orders (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_status status DEFAULT 'new',
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- 1.4.1 Таблица элементов заказа
CREATE TABLE order_items (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL, -- Цена на момент продажи
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Категории
INSERT INTO categories (name, parent_id) VALUES
('Электроника', NULL),
('Смартфоны', 1),
('Ноутбуки', 1),
('Телевизоры', 1),
('Одежда', NULL),
('Мужская одежда', 5),
('Женская одежда', 5),
('Обувь', 5),
('Бытовая техника', NULL),
('Холодильники', 9),
('Стиральные машины', 9);

-- Покупатели
INSERT INTO customers (name, address) VALUES
('Иван Петров', 'ул. Ленина, 15, Москва'),
('Мария Сидорова', 'пр. Победы, 23, Санкт-Петербург'),
('Алексей Козлов', 'ул. Садовая, 7, Казань'),
('Елена Волкова', 'ул. Центральная, 12, Новосибирск'),
('Дмитрий Смирнов', 'пр. Мира, 45, Екатеринбург');

-- Товары
INSERT INTO products (name, quantity, price, category_id) VALUES
('iPhone 14 Pro', 25, 89990, 2),
('Samsung Galaxy S23', 18, 74990, 2),
('MacBook Air M2', 12, 119990, 3),
('Dell XPS 13', 8, 89990, 3),
('Samsung QLED 55"', 15, 65990, 4),
('LG OLED 65"', 10, 89990, 4),
('Джинсы Levi''s', 50, 4990, 6),
('Платье летнее', 35, 3490, 7),
('Кроссовки Nike', 40, 5990, 8),
('Холодильник Bosch', 6, 45990, 10),
('Стиральная машина LG', 7, 32990, 11);

-- Заказы
INSERT INTO orders (order_date, current_status, customer_id) VALUES
('2025-08-15', 'delivered', 1),
('2025-08-16', 'processing', 2),
('2025-08-17', 'shipped', 3),
('2025-08-18', 'delivered', 4),
('2025-08-19', 'processing', 5),
('2025-08-20', 'shipped', 1);

-- Элементы заказов
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 89990),
(1, 9, 1, 5990),
(2, 3, 1, 119990),
(2, 5, 1, 65990),
(3, 7, 2, 4990),
(3, 8, 1, 3490),
(4, 10, 1, 45990),
(4, 11, 1, 32990),
(5, 2, 1, 74990),
(5, 4, 1, 89990),
(6, 6, 1, 89990),
(6, 9, 2, 5990);