CREATE TABLE IF NOT EXISTS customers (
    customer_id             VARCHAR(50)  NOT NULL,
    customer_unique_id      VARCHAR(50)  NOT NULL,
    customer_zip_code_prefix INT,
    customer_city           VARCHAR(100),
    customer_state          VARCHAR(10),
    PRIMARY KEY (customer_id)
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id               VARCHAR(50)  NOT NULL,
    seller_zip_code_prefix  INT,
    seller_city             VARCHAR(100),
    seller_state            VARCHAR(10),
    PRIMARY KEY (seller_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id                  VARCHAR(50)  NOT NULL,
    product_category_name       VARCHAR(150),
    product_name_length         INT,
    product_description_length  INT,
    product_photos_qty          INT,
    product_weight_g            DECIMAL(12,2),
    product_length_cm           DECIMAL(12,2),
    product_height_cm           DECIMAL(12,2),
    product_width_cm            DECIMAL(12,2),
    PRIMARY KEY (product_id)
);

CREATE TABLE IF NOT EXISTS category_translation (
    product_category_name         VARCHAR(150) NOT NULL,
    product_category_name_english VARCHAR(150),
    PRIMARY KEY (product_category_name)
);

CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix INT,
    geolocation_lat             DECIMAL(10,7),
    geolocation_lng             DECIMAL(10,7),
    geolocation_city            VARCHAR(100),
    geolocation_state           VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id                      VARCHAR(50) NOT NULL,
    customer_id                   VARCHAR(50) NOT NULL,
    order_status                  VARCHAR(30),
    order_purchase_timestamp      DATETIME,
    order_approved_at             DATETIME,
    order_delivered_carrier_date  DATETIME,
    order_delivered_customer_date DATETIME,
    order_estimated_delivery_date DATETIME,
    PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON orders(customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_purchase_date
    ON orders(order_purchase_timestamp);

CREATE TABLE IF NOT EXISTS order_items (
    order_id            VARCHAR(50)   NOT NULL,
    order_item_id       INT           NOT NULL,
    product_id          VARCHAR(50),
    seller_id           VARCHAR(50),
    shipping_limit_date DATETIME,
    price               DECIMAL(12,2),
    freight_value       DECIMAL(12,2),
    PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)    REFERENCES orders(order_id),
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)  REFERENCES products(product_id),
    CONSTRAINT fk_order_items_seller
        FOREIGN KEY (seller_id)   REFERENCES sellers(seller_id)
);

CREATE INDEX IF NOT EXISTS idx_order_items_product
    ON order_items(product_id);

CREATE INDEX IF NOT EXISTS idx_order_items_seller
    ON order_items(seller_id);

CREATE TABLE IF NOT EXISTS payments (
    order_id             VARCHAR(50)  NOT NULL,
    payment_sequential   INT          NOT NULL,
    payment_type         VARCHAR(50),
    payment_installments INT,
    payment_value        DECIMAL(12,2),
    PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id               VARCHAR(50)  NOT NULL,
    order_id                VARCHAR(50)  NOT NULL,
    review_score            INT,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    DATETIME,
    review_answer_timestamp DATETIME,
    PRIMARY KEY (review_id, order_id),
    CONSTRAINT fk_reviews_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
