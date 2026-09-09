CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key       INT          NOT NULL AUTO_INCREMENT,
    customer_id        VARCHAR(50)  NOT NULL,
    customer_unique_id VARCHAR(50),
    customer_city      VARCHAR(100),
    customer_state     VARCHAR(10),
    PRIMARY KEY (customer_key),
    UNIQUE KEY uq_dim_customer_id (customer_id)
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key           INT          NOT NULL AUTO_INCREMENT,
    product_id            VARCHAR(50)  NOT NULL,
    category_name         VARCHAR(150),
    category_name_english VARCHAR(150),
    PRIMARY KEY (product_key),
    UNIQUE KEY uq_dim_product_id (product_id)
);

CREATE TABLE IF NOT EXISTS dim_seller (
    seller_key   INT          NOT NULL AUTO_INCREMENT,
    seller_id    VARCHAR(50)  NOT NULL,
    seller_city  VARCHAR(100),
    seller_state VARCHAR(10),
    PRIMARY KEY (seller_key),
    UNIQUE KEY uq_dim_seller_id (seller_id)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key   INT         NOT NULL,
    full_date  DATE,
    year       INT,
    quarter    INT,
    month      INT,
    month_name VARCHAR(20),
    week       INT,
    day        INT,
    PRIMARY KEY (date_key)
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key       BIGINT       NOT NULL AUTO_INCREMENT,
    order_id        VARCHAR(50),
    order_item_id   INT,
    customer_key    INT,
    product_key     INT,
    seller_key      INT,
    date_key        INT,
    quantity        INT          NOT NULL DEFAULT 1,
    product_price   DECIMAL(12,2),
    freight_value   DECIMAL(12,2),
    total_item_value DECIMAL(12,2),
    PRIMARY KEY (sales_key),
    CONSTRAINT fk_fact_customer
        FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    CONSTRAINT fk_fact_product
        FOREIGN KEY (product_key)  REFERENCES dim_product(product_key),
    CONSTRAINT fk_fact_seller
        FOREIGN KEY (seller_key)   REFERENCES dim_seller(seller_key),
    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key)     REFERENCES dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_date_key
    ON fact_sales(date_key);

CREATE INDEX IF NOT EXISTS idx_fact_customer_key
    ON fact_sales(customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_product_key
    ON fact_sales(product_key);
