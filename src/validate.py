from pathlib import Path
import pandas as pd


PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def require_columns(df: pd.DataFrame, required: list[str], context: str = "") -> None:
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(
            f"[{context}] Missing required columns: {missing}"
        )


def export_rejected(df: pd.DataFrame, filename: str) -> None:
    if df.empty:
        return
    path = PROCESSED_DIR / filename
    df.to_csv(path, index=False)


def validate_customers(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, ["customer_id", "customer_unique_id"], "customers")

    if df["customer_id"].isnull().any():
        raise ValueError("customers: null customer_id detected.")

    if df["customer_unique_id"].isnull().any():
        raise ValueError("customers: null customer_unique_id detected.")

    return df


def validate_orders(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        df,
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
        "orders",
    )

    if df["order_id"].isnull().any():
        raise ValueError("orders: null order_id detected.")

    if df["order_id"].duplicated().any():
        raise ValueError("orders: duplicate order_id detected.")

    if df["customer_id"].isnull().any():
        raise ValueError("orders: null customer_id detected.")

    return df


def validate_order_items(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    require_columns(
        df,
        ["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"],
        "order_items",
    )

    invalid_price = df["price"].isnull() | (df["price"] < 0)
    invalid_freight = df["freight_value"].isnull() | (df["freight_value"] < 0)
    rejected_mask = invalid_price | invalid_freight

    rejected = df[rejected_mask].copy()
    valid = df[~rejected_mask].copy()

    export_rejected(rejected, "rejected_order_items.csv")

    return valid, rejected


def validate_payments(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    require_columns(df, ["order_id", "payment_type", "payment_value"], "payments")

    invalid_value = df["payment_value"].isnull() | (df["payment_value"] < 0)
    invalid_installments = df["payment_installments"].isnull() | (
        df["payment_installments"] < 0
    )
    rejected_mask = invalid_value | invalid_installments

    rejected = df[rejected_mask].copy()
    valid = df[~rejected_mask].copy()

    export_rejected(rejected, "rejected_payments.csv")

    return valid, rejected


def validate_products(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, ["product_id"], "products")

    if df["product_id"].isnull().any():
        raise ValueError("products: null product_id detected.")

    if df["product_id"].duplicated().any():
        raise ValueError("products: duplicate product_id detected.")

    return df


def validate_reviews(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    require_columns(df, ["review_id", "order_id", "review_score"], "reviews")

    invalid_score = df["review_score"].isnull() | ~df["review_score"].between(1, 5)
    rejected = df[invalid_score].copy()
    valid = df[~invalid_score].copy()

    export_rejected(rejected, "rejected_reviews.csv")

    return valid, rejected
