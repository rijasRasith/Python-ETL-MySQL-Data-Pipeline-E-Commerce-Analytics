from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")


def read_csv(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Expected raw file not found: {path}\n"
            "Download the Olist dataset and place the CSVs in data/raw/."
        )

    return pd.read_csv(path, low_memory=False)


def extract_all() -> dict[str, pd.DataFrame]:
    return {
        "customers": read_csv("olist_customers_dataset.csv"),
        "geolocation": read_csv("olist_geolocation_dataset.csv"),
        "order_items": read_csv("olist_order_items_dataset.csv"),
        "payments": read_csv("olist_order_payments_dataset.csv"),
        "reviews": read_csv("olist_order_reviews_dataset.csv"),
        "orders": read_csv("olist_orders_dataset.csv"),
        "products": read_csv("olist_products_dataset.csv"),
        "sellers": read_csv("olist_sellers_dataset.csv"),
        "category_translation": read_csv("product_category_name_translation.csv"),
    }


def profile_datasets(data: dict[str, pd.DataFrame]) -> None:
    for name, df in data.items():
        print(f"\n{'=' * 50}")
        print(f"  {name.upper()}")
        print(f"{'=' * 50}")
        print(f"  Rows       : {len(df):,}")
        print(f"  Columns    : {len(df.columns)}")
        print(f"  Duplicates : {df.duplicated().sum():,}")
        null_totals = df.isnull().sum()
        null_cols = null_totals[null_totals > 0]
        if not null_cols.empty:
            print("  Nulls per column:")
            for col, cnt in null_cols.items():
                print(f"    {col}: {cnt:,}")
        else:
            print("  Nulls      : None")
