-- ============================================================
-- OLIST E-COMMERCE — SQL ANALYTICS
-- ============================================================


-- ------------------------------------------------------------
-- REVENUE
-- ------------------------------------------------------------

-- Total product revenue
SELECT
    SUM(price) AS total_product_revenue
FROM order_items;


-- Total freight revenue
SELECT
    SUM(freight_value) AS total_freight_revenue
FROM order_items;


-- Gross order value (product + freight)
SELECT
    SUM(price + freight_value) AS gross_order_value
FROM order_items;


-- Average order value
SELECT
    SUM(order_value) / COUNT(DISTINCT order_id) AS average_order_value
FROM (
    SELECT
        order_id,
        SUM(price + freight_value) AS order_value
    FROM order_items
    GROUP BY order_id
) sub;


-- Monthly revenue
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
    SUM(oi.price)                                    AS product_revenue,
    SUM(oi.price + oi.freight_value)                 AS gross_revenue
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
GROUP BY month
ORDER BY month;


-- Revenue by customer state
SELECT
    c.customer_state,
    SUM(oi.price)                    AS product_revenue,
    SUM(oi.price + oi.freight_value) AS gross_revenue,
    COUNT(DISTINCT o.order_id)       AS order_count
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
GROUP BY c.customer_state
ORDER BY gross_revenue DESC;


-- ------------------------------------------------------------
-- PRODUCTS & CATEGORIES
-- ------------------------------------------------------------

-- Top 10 products by revenue
SELECT
    oi.product_id,
    SUM(oi.price)              AS product_revenue,
    COUNT(oi.order_item_id)    AS units_sold
FROM order_items oi
GROUP BY oi.product_id
ORDER BY product_revenue DESC
LIMIT 10;


-- Revenue by category (with English translation)
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    SUM(oi.price)                                                        AS product_revenue,
    COUNT(oi.order_item_id)                                              AS units_sold
FROM products p
JOIN order_items oi
    ON p.product_id = oi.product_id
LEFT JOIN category_translation t
    ON p.product_category_name = t.product_category_name
GROUP BY category
ORDER BY product_revenue DESC;


-- ------------------------------------------------------------
-- SELLERS
-- ------------------------------------------------------------

-- Top 20 sellers by revenue
SELECT
    seller_id,
    SUM(price)                  AS seller_revenue,
    COUNT(DISTINCT order_id)    AS order_count,
    COUNT(order_item_id)        AS items_sold
FROM order_items
GROUP BY seller_id
ORDER BY seller_revenue DESC
LIMIT 20;


-- Sellers with high revenue but below-average review scores
SELECT
    oi.seller_id,
    SUM(oi.price)      AS revenue,
    AVG(r.review_score) AS avg_review_score
FROM order_items oi
JOIN reviews r
    ON oi.order_id = r.order_id
GROUP BY oi.seller_id
HAVING
    revenue > (SELECT AVG(seller_revenue) FROM (
        SELECT seller_id, SUM(price) AS seller_revenue
        FROM order_items
        GROUP BY seller_id
    ) sub)
    AND avg_review_score < 3
ORDER BY revenue DESC;


-- ------------------------------------------------------------
-- PAYMENTS
-- ------------------------------------------------------------

-- Payment method distribution
SELECT
    payment_type,
    COUNT(*)              AS transaction_count,
    SUM(payment_value)    AS total_payment_value,
    AVG(payment_value)    AS avg_payment_value,
    AVG(payment_installments) AS avg_installments
FROM payments
GROUP BY payment_type
ORDER BY total_payment_value DESC;


-- ------------------------------------------------------------
-- CUSTOMERS
-- ------------------------------------------------------------

-- Repeat customers (using customer_unique_id)
SELECT
    c.customer_unique_id,
    COUNT(o.order_id) AS order_count
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_unique_id
HAVING COUNT(o.order_id) > 1
ORDER BY order_count DESC;


-- Repeat customer percentage
SELECT
    100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
            / COUNT(*) AS repeat_customer_percentage
FROM (
    SELECT
        c.customer_unique_id,
        COUNT(o.order_id) AS order_count
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
) sub;


-- Top 20 customers by lifetime value
SELECT
    c.customer_unique_id,
    SUM(oi.price + oi.freight_value) AS lifetime_value,
    COUNT(DISTINCT o.order_id)        AS total_orders
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
GROUP BY c.customer_unique_id
ORDER BY lifetime_value DESC
LIMIT 20;


-- ------------------------------------------------------------
-- DELIVERY PERFORMANCE
-- ------------------------------------------------------------

-- Average delivery time (days)
SELECT
    AVG(DATEDIFF(
        order_delivered_customer_date,
        order_purchase_timestamp
    )) AS avg_delivery_days
FROM orders
WHERE order_delivered_customer_date IS NOT NULL;


-- Total late orders
SELECT
    COUNT(*) AS late_order_count
FROM orders
WHERE
    order_delivered_customer_date IS NOT NULL
    AND order_delivered_customer_date > order_estimated_delivery_date;


-- Late delivery percentage
SELECT
    100.0 * SUM(
        CASE
            WHEN order_delivered_customer_date > order_estimated_delivery_date
            THEN 1 ELSE 0
        END
    ) / COUNT(*) AS late_delivery_percentage
FROM orders
WHERE order_delivered_customer_date IS NOT NULL;


-- Delivery performance by state
SELECT
    c.customer_state,
    AVG(DATEDIFF(
        o.order_delivered_customer_date,
        o.order_purchase_timestamp
    ))                         AS avg_delivery_days,
    COUNT(o.order_id)          AS delivered_orders,
    100.0 * SUM(
        CASE
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN 1 ELSE 0
        END
    ) / COUNT(*)               AS late_pct
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC;


-- ------------------------------------------------------------
-- REVIEWS & SATISFACTION
-- ------------------------------------------------------------

-- Overall average review score
SELECT
    AVG(review_score)                              AS avg_review_score,
    COUNT(*)                                       AS total_reviews,
    SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END) AS five_star_count
FROM reviews;


-- Review score vs delivery status
SELECT
    CASE
        WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
        THEN 'Late'
        ELSE 'On Time'
    END                    AS delivery_status,
    AVG(r.review_score)    AS avg_review_score,
    COUNT(r.review_id)     AS review_count
FROM orders o
JOIN reviews r
    ON o.order_id = r.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery_status;


-- ------------------------------------------------------------
-- REFERENTIAL INTEGRITY CHECKS
-- ------------------------------------------------------------

-- Orders with no matching customer (expect 0)
SELECT COUNT(*) AS orphan_orders
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;


-- Order items with no matching order (expect 0)
SELECT COUNT(*) AS orphan_order_items
FROM order_items oi
LEFT JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;


-- Order items with no matching product (expect 0)
SELECT COUNT(*) AS orphan_products
FROM order_items oi
LEFT JOIN products p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;
