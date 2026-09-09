import pandas as pd


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w]", "_", regex=True)
    )
    return df


def convert_datetime_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def coerce_numeric_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)
    df = df.drop_duplicates(subset=["customer_id"])
    return df


def transform_sellers(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)
    df = df.drop_duplicates(subset=["seller_id"])
    return df


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)

    numeric_cols = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    df = coerce_numeric_columns(df, numeric_cols)

    df.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        },
        inplace=True,
    )

    df = df.drop_duplicates(subset=["product_id"])
    return df


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)

    datetime_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    df = convert_datetime_columns(df, datetime_cols)
    df = df.drop_duplicates(subset=["order_id"])
    return df


def transform_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)
    df = coerce_numeric_columns(df, ["price", "freight_value"])

    if "shipping_limit_date" in df.columns:
        df = convert_datetime_columns(df, ["shipping_limit_date"])

    df = df.drop_duplicates(subset=["order_id", "order_item_id"])
    return df


def transform_payments(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)
    df = coerce_numeric_columns(df, ["payment_value", "payment_installments"])
    return df


def transform_reviews(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)
    df = coerce_numeric_columns(df, ["review_score"])
    df = convert_datetime_columns(
        df, ["review_creation_date", "review_answer_timestamp"]
    )
    return df


def transform_categories(df: pd.DataFrame) -> pd.DataFrame:
    return clean_column_names(df)


def transform_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_column_names(df)
    df = coerce_numeric_columns(df, ["geolocation_lat", "geolocation_lng"])
    df = df.drop_duplicates()
    return df
