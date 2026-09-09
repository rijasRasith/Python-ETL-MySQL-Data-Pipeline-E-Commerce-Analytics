import time
import textwrap
from pathlib import Path
from datetime import datetime

from src.utils import logger
from src.extract import extract_all
from src.transform import (
    transform_customers,
    transform_sellers,
    transform_products,
    transform_orders,
    transform_order_items,
    transform_payments,
    transform_reviews,
    transform_categories,
    transform_geolocation,
)
from src.validate import (
    validate_customers,
    validate_orders,
    validate_order_items,
    validate_payments,
    validate_products,
    validate_reviews,
)
from src.load import (
    load_dataframe,
    execute_sql_file,
    reconcile,
    update_etl_metadata,
)


PIPELINE_NAME = "olist_etl_pipeline"
SQL_DIR = Path("sql")


def _elapsed(start: float) -> str:
    return f"{time.perf_counter() - start:.2f}s"


def _print_banner(title: str) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def _print_quality_report(report: list[dict], total_elapsed: str) -> None:
    _print_banner("ETL DATA QUALITY REPORT")
    header = f"{'Table':<25} {'Source':>10} {'Target':>10} {'Rejected':>10} {'Status':>8}"
    print(header)
    print("-" * len(header))
    for row in report:
        rejected = row.get("rejected_count", 0)
        print(
            f"{row['table']:<25} "
            f"{row['source_count']:>10,} "
            f"{row['target_count']:>10,} "
            f"{rejected:>10,} "
            f"{row['status']:>8}"
        )
    all_pass = all(r["status"] == "PASS" for r in report)
    print("-" * len(header))
    print(f"\n  Overall status : {'SUCCESS' if all_pass else 'FAILURE'}")
    print(f"  Execution time : {total_elapsed}")
    print("=" * 60)


def _bootstrap_schema() -> None:
    logger.info("Bootstrapping database schema from SQL files.")
    for filename in ("database.sql", "staging.sql", "oltp.sql", "olap.sql"):
        path = SQL_DIR / filename
        if path.exists():
            execute_sql_file(str(path))
            logger.info("Executed schema file: %s", filename)
        else:
            logger.warning("Schema file not found, skipping: %s", filename)


def run_pipeline() -> None:
    pipeline_start = time.perf_counter()
    quality_report: list[dict] = []
    pipeline_status = "SUCCESS"

    try:
        _print_banner("OLIST ETL PIPELINE — STARTING")
        logger.info("Pipeline run started at %s", datetime.now().isoformat())

        _bootstrap_schema()

        t0 = time.perf_counter()
        logger.info("EXTRACT — reading source CSV files.")
        raw = extract_all()
        logger.info("Extraction completed in %s.", _elapsed(t0))

        t0 = time.perf_counter()
        logger.info("TRANSFORM — cleaning and normalizing all entities.")

        customers = transform_customers(raw["customers"])
        sellers = transform_sellers(raw["sellers"])
        products = transform_products(raw["products"])
        orders = transform_orders(raw["orders"])
        order_items = transform_order_items(raw["order_items"])
        payments = transform_payments(raw["payments"])
        reviews = transform_reviews(raw["reviews"])
        categories = transform_categories(raw["category_translation"])
        geolocation = transform_geolocation(raw["geolocation"])

        logger.info("Transformation completed in %s.", _elapsed(t0))

        t0 = time.perf_counter()
        logger.info("VALIDATE — applying schema and business rule checks.")

        validate_customers(customers)
        validate_orders(orders)
        validate_products(products)

        order_items, rejected_items = validate_order_items(order_items)
        payments, rejected_payments = validate_payments(payments)
        reviews, rejected_reviews = validate_reviews(reviews)

        logger.info(
            "Rejected records — order_items: %d, payments: %d, reviews: %d.",
            len(rejected_items),
            len(rejected_payments),
            len(rejected_reviews),
        )
        logger.info("Validation completed in %s.", _elapsed(t0))

        t0 = time.perf_counter()
        logger.info("LOAD — writing data to MySQL (replace mode for full refresh).")

        load_sequence = [
            (customers,    "customers",            "replace"),
            (sellers,      "sellers",              "replace"),
            (products,     "products",             "replace"),
            (categories,   "category_translation", "replace"),
            (geolocation,  "geolocation",          "replace"),
            (orders,       "orders",               "replace"),
            (order_items,  "order_items",          "replace"),
            (payments,     "payments",             "replace"),
            (reviews,      "reviews",              "replace"),
        ]

        for df, table, mode in load_sequence:
            load_dataframe(df, table, mode)
            logger.info("Loaded table '%s'.", table)

        logger.info("Load completed in %s.", _elapsed(t0))

        t0 = time.perf_counter()
        logger.info("RECONCILE — verifying source vs target row counts.")

        recon_targets = [
            (customers,   "customers"),
            (sellers,     "sellers"),
            (products,    "products"),
            (orders,      "orders"),
            (order_items, "order_items"),
            (payments,    "payments"),
            (reviews,     "reviews"),
        ]

        for df, table in recon_targets:
            result = reconcile(df, table, context="pipeline")
            rejected_count = 0
            if table == "order_items":
                rejected_count = len(rejected_items)
            elif table == "payments":
                rejected_count = len(rejected_payments)
            elif table == "reviews":
                rejected_count = len(rejected_reviews)
            result["rejected_count"] = rejected_count
            quality_report.append(result)

        logger.info("Reconciliation completed in %s.", _elapsed(t0))

        logger.info("OLAP — populating star schema dimensions and fact table.")
        _populate_olap()
        logger.info("OLAP population completed.")

    except Exception as exc:
        pipeline_status = "FAILURE"
        logger.exception("Pipeline encountered a fatal error: %s", exc)
        raise

    finally:
        total_elapsed = _elapsed(pipeline_start)
        _print_quality_report(quality_report, total_elapsed)

        try:
            update_etl_metadata(PIPELINE_NAME, pipeline_status)
        except Exception:
            logger.warning("Failed to update ETL metadata table.", exc_info=True)

        logger.info(
            "Pipeline finished with status '%s' in %s.",
            pipeline_status,
            total_elapsed,
        )


def _populate_olap() -> None:
    from sqlalchemy import text
    from src.database import engine

    dim_customer_sql = """
        INSERT INTO dim_customer
            (customer_id, customer_unique_id, customer_city, customer_state)
        SELECT
            customer_id,
            customer_unique_id,
            customer_city,
            customer_state
        FROM customers
        ON DUPLICATE KEY UPDATE
            customer_unique_id = VALUES(customer_unique_id),
            customer_city      = VALUES(customer_city),
            customer_state     = VALUES(customer_state)
    """

    dim_product_sql = """
        INSERT INTO dim_product
            (product_id, category_name, category_name_english)
        SELECT
            p.product_id,
            p.product_category_name,
            COALESCE(t.product_category_name_english, p.product_category_name)
        FROM products p
        LEFT JOIN category_translation t
            ON p.product_category_name = t.product_category_name
        ON DUPLICATE KEY UPDATE
            category_name         = VALUES(category_name),
            category_name_english = VALUES(category_name_english)
    """

    dim_seller_sql = """
        INSERT INTO dim_seller
            (seller_id, seller_city, seller_state)
        SELECT
            seller_id,
            seller_city,
            seller_state
        FROM sellers
        ON DUPLICATE KEY UPDATE
            seller_city  = VALUES(seller_city),
            seller_state = VALUES(seller_state)
    """

    dim_date_sql = """
        INSERT IGNORE INTO dim_date
            (date_key, full_date, year, quarter, month, month_name, week, day)
        SELECT DISTINCT
            CAST(DATE_FORMAT(order_purchase_timestamp, '%Y%m%d') AS UNSIGNED) AS date_key,
            DATE(order_purchase_timestamp)                                     AS full_date,
            YEAR(order_purchase_timestamp)                                     AS year,
            QUARTER(order_purchase_timestamp)                                  AS quarter,
            MONTH(order_purchase_timestamp)                                    AS month,
            MONTHNAME(order_purchase_timestamp)                                AS month_name,
            WEEK(order_purchase_timestamp, 1)                                  AS week,
            DAY(order_purchase_timestamp)                                      AS day
        FROM orders
        WHERE order_purchase_timestamp IS NOT NULL
    """

    fact_sales_sql = """
        INSERT INTO fact_sales
            (order_id, order_item_id, customer_key, product_key, seller_key,
             date_key, quantity, product_price, freight_value, total_item_value)
        SELECT
            oi.order_id,
            oi.order_item_id,
            dc.customer_key,
            dp.product_key,
            ds.seller_key,
            CAST(DATE_FORMAT(o.order_purchase_timestamp, '%Y%m%d') AS UNSIGNED) AS date_key,
            1                                                                    AS quantity,
            oi.price                                                             AS product_price,
            oi.freight_value,
            oi.price + oi.freight_value                                          AS total_item_value
        FROM order_items oi
        JOIN orders o
            ON oi.order_id = o.order_id
        JOIN dim_customer dc
            ON o.customer_id = dc.customer_id
        JOIN dim_product dp
            ON oi.product_id = dp.product_id
        JOIN dim_seller ds
            ON oi.seller_id = ds.seller_id
        WHERE o.order_purchase_timestamp IS NOT NULL
    """

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_sales"))
        conn.execute(text("DELETE FROM dim_customer"))
        conn.execute(text("DELETE FROM dim_product"))
        conn.execute(text("DELETE FROM dim_seller"))
        conn.execute(text("DELETE FROM dim_date"))

        conn.execute(text(dim_customer_sql))
        conn.execute(text(dim_product_sql))
        conn.execute(text(dim_seller_sql))
        conn.execute(text(dim_date_sql))
        conn.execute(text(fact_sales_sql))


if __name__ == "__main__":
    run_pipeline()
