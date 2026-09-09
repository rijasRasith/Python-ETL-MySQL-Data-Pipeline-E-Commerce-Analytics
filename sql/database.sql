CREATE DATABASE IF NOT EXISTS olist_etl
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE olist_etl;

CREATE TABLE IF NOT EXISTS etl_metadata (
    pipeline_name            VARCHAR(100) PRIMARY KEY,
    last_successful_run      DATETIME,
    last_processed_timestamp DATETIME,
    status                   VARCHAR(20)
);
