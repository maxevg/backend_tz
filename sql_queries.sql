-- Сумма товаров по клиентам
SELECT 
    c.name AS client,
    SUM(oi.quantity * oi.price) AS amount
FROM customers c
INNER JOIN orders o ON o.customer_id = c.id
INNER JOIN order_items oi ON oi.order_id = o.id
GROUP BY c.id, c.name
ORDER BY SUM(oi.quantity * oi.price) DESC;

-- Количество дочерних элементов первого уровня
SELECT 
    parent.id AS category_ID,
    parent.name AS category,
    COUNT(child.id) AS child_num
FROM categories parent
LEFT JOIN categories child ON child.parent_id = parent.id
GROUP BY parent.id, parent.name
ORDER BY parent.name;

-- Топ-5 самых покупаемых товаров
CREATE VIEW top_5_products_last_month AS
SELECT
    p.name AS product,
    root_category.name AS category_1_lvl,
    SUM(oi.quantity) AS sold_amount
FROM order_items oi
INNER JOIN orders o ON oi.order_id = o.id
INNER JOIN products p ON oi.product_id = p.id
INNER JOIN categories cat ON p.category_id = cat.id
LEFT JOIN categories root_category ON (
    -- Если у категории нет родителя, то она корневая и берем ее саму
    -- Иначе идем вверх по иерархии, пока не найдем корень
    root_category.id = (
        WITH RECURSIVE category_path AS (
            SELECT id, parent_id, name
            FROM categories
            WHERE id = cat.id
            UNION ALL
            SELECT c.id, c.parent_id, c.name
            FROM categories c
            INNER JOIN category_path cp ON c.id = cp.parent_id
        )
        SELECT id FROM category_path WHERE parent_id IS NULL
    )
)
WHERE o.order_date >= NOW() - INTERVAL '1 month'
    AND o.order_date < NOW()
GROUP BY p.id, p.name, root_category.name
ORDER BY SUM(oi.quantity) DESC
LIMIT 5;

/*
    Оптимизация:
    1. Добавить в таблицу categories поле для хранения корневой категории сразу
    2. Отказ от VIEW в пользу таблиц для хранения результатов, т.к. VIEW выполняется каждый раз при обращении к ней.
    3. Использование иных способов хранения дерева вместо Adjacency List.
    4. В последствии выносить исторические данные из 'горячих' таблиц
*/