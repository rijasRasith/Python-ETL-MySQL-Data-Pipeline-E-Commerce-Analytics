# Python ETL & MySQL Data Pipeline

End-to-end data engineering pipeline using the **Brazilian E-Commerce Public Dataset by Olist** (~100,000 orders). Built to demonstrate production-style ETL, normalized OLTP modeling, dimensional OLAP design, SQL analytics, and automated data quality assurance.

---

## Architecture

```
OLIST CSV DATASET
      │
      ▼
EXTRACT LAYER          ← src/extract.py
      │
      ▼
VALIDATION LAYER       ← src/validate.py  (schema + business rules)
      │
      ▼
TRANSFORMATION LAYER   ← src/transform.py (clean, coerce, deduplicate)
      │
      ▼
MYSQL STAGING          ← sql/staging.sql  (stg_* tables)
      │
      ▼
MYSQL OLTP             ← sql/oltp.sql     (normalized schema + FK constraints)
      │
      ▼
MYSQL OLAP             ← sql/olap.sql     (star schema: dims + fact_sales)
      │
      ▼
SQL ANALYTICS          ← sql/analytics.sql
      │
      ▼
POWER BI DASHBOARD
```

---

## Dataset

**Brazilian E-Commerce Public Dataset by Olist**  
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce  
License: CC BY-NC-SA 4.0

Files required in `data/raw/`:

```
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
```

---

## Technologies

| Layer          | Technology                          |
|----------------|--------------------------------------|
| Language       | Python 3.11+                        |
| Data processing | Pandas, NumPy                       |
| Database       | MySQL 8                             |
| ORM / Connector | SQLAlchemy 2 + PyMySQL             |
| Configuration  | python-dotenv                       |
| Testing        | pytest                              |
| Analytics      | SQL                                 |
| Visualization  | Power BI                            |
| Version control | Git + GitHub                       |

---

## Project Structure

```
python-mysql-etl/
├── data/
│   ├── raw/               ← Olist CSV files (not committed)
│   └── processed/         ← Rejected record exports
├── logs/
├── sql/
│   ├── database.sql       ← Database + etl_metadata
│   ├── staging.sql        ← Staging tables
│   ├── oltp.sql           ← Normalized OLTP schema
│   ├── olap.sql           ← Star schema (dims + fact)
│   └── analytics.sql      ← Business analytics queries
├── src/
│   ├── config.py          ← Environment variable loading
│   ├── database.py        ← SQLAlchemy engine
│   ├── extract.py         ← CSV extraction
│   ├── transform.py       ← Cleaning + normalization
│   ├── validate.py        ← Business rule validation
│   ├── load.py            ← Database loading + reconciliation
│   ├── pipeline.py        ← Pipeline orchestrator
│   └── utils.py           ← Logger
├── tests/
│   ├── test_transform.py
│   └── test_validate.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Database Design

### OLTP (Normalized)

```
customers ──► orders ──► order_items ──► products
                    └──► payments          └──► sellers
                    └──► reviews
```

### OLAP (Star Schema)

```
dim_date ─┐
dim_customer ─┤
              ├─► fact_sales
dim_product ──┤
dim_seller ───┘
```

**Grain:** One row in `fact_sales` = one product item within one Olist order.

---

## ETL Process

| Stage        | Description                                                              |
|--------------|--------------------------------------------------------------------------|
| Extract      | Read all 9 Olist CSVs into Pandas DataFrames                            |
| Validate     | Schema checks, null/duplicate detection, business rule enforcement       |
| Transform    | Column normalization, type coercion, deduplication, datetime parsing     |
| Load         | Bulk insert into MySQL staging → OLTP → OLAP via SQLAlchemy             |
| Reconcile    | Source row count verified against target after every load                |

---

## Data Quality

- Schema validation per entity (required columns enforced)
- Null checks on primary keys and business-critical fields
- Duplicate detection and deduplication
- Business rule enforcement (price ≥ 0, payment_value ≥ 0, review_score 1–5)
- Rejected records exported to `data/processed/`
- Source-to-target reconciliation after load
- ETL metadata table tracks run status and timestamps

---

## Installation

```powershell
# Clone and enter project
git clone <repository-url>
cd python-mysql-etl

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env
# Edit .env with your MySQL credentials
```

Create the MySQL database:

```sql
CREATE DATABASE olist_etl CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Place Olist CSV files in `data/raw/`.

---

## Running the Pipeline

```powershell
python -m src.pipeline
```

Expected output:

```
============================================================
  OLIST ETL PIPELINE — STARTING
============================================================
...
============================================================
  ETL DATA QUALITY REPORT
============================================================
Table                      Source     Target   Rejected   Status
------------------------------------------------------------------
customers                  99441      99441          0     PASS
...
Overall status : SUCCESS
Execution time : 45.32s
============================================================
```

---

## Testing

```powershell
pytest -v
```

---

## SQL Analytics

Open `sql/analytics.sql` in MySQL Workbench or any SQL client to explore:

- Total and monthly revenue
- Revenue by state, category, and seller
- Customer lifetime value and repeat purchase rate
- Delivery performance (avg days, late delivery %)
- Review score vs delivery status
- Payment method distribution

---

## Power BI Dashboard

Connect Power BI Desktop to MySQL using the MySQL ODBC connector.

Recommended pages:
1. **Executive Overview** — KPI cards + revenue trends
2. **Sales** — Top products, categories, sellers
3. **Customers** — Repeat customers, CLV, geographic distribution
4. **Delivery** — Delivery times, late %, performance by state
5. **Payments** — Payment method split, installment distribution

---

## Future Improvements

- Incremental ETL with watermark-based extraction
- SCD Type 2 dimensions for customer and product history
- Apache Airflow DAG for scheduled orchestration
- Docker containerization
- GitHub Actions CI/CD with automated pytest on push
- Great Expectations for declarative data quality rules
- dbt models for warehouse transformations

---

## Author

Portfolio Data Engineering Project  
Dataset: Olist Brazilian E-Commerce (CC BY-NC-SA 4.0)
