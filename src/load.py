import pandas as pd
from sqlalchemy import text
from src.database import engine
from src.utils import logger


def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "append",
) -> int:
    df.to_sql(
        table_name,
        con=engine,
        if_exists=if_exists,
        index=False,
        chunksize=5000,
        method="multi",
    )
    row_count = len(df)
    logger.debug("Loaded %d rows into table '%s'.", row_count, table_name)
    return row_count


def execute_sql(sql: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql))


def execute_sql_file(path: str) -> None:
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()

    statements = [s.strip() for s in raw.split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def reconcile(
    df: pd.DataFrame,
    table_name: str,
    context: str = "",
) -> dict:
    source_count = len(df)

    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
        target_count = result.scalar()

    status = "PASS" if source_count == target_count else "FAIL"

    if status == "FAIL":
        logger.warning(
            "[%s] Reconciliation FAILED for '%s': source=%d, target=%d",
            context,
            table_name,
            source_count,
            target_count,
        )
    else:
        logger.info(
            "[%s] Reconciliation PASSED for '%s': %d rows.",
            context,
            table_name,
            source_count,
        )

    return {
        "table": table_name,
        "source_count": source_count,
        "target_count": target_count,
        "status": status,
    }


def update_etl_metadata(
    pipeline_name: str,
    status: str,
    last_processed_ts=None,
) -> None:
    sql = text(
        """
        INSERT INTO etl_metadata
            (pipeline_name, last_successful_run, last_processed_timestamp, status)
        VALUES
            (:name, NOW(), :ts, :status)
        ON DUPLICATE KEY UPDATE
            last_successful_run = NOW(),
            last_processed_timestamp = :ts,
            status = :status
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {"name": pipeline_name, "ts": last_processed_ts, "status": status},
        )
