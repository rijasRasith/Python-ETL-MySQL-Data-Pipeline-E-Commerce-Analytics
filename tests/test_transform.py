import pandas as pd
import pytest

from src.transform import (
    clean_column_names,
    coerce_numeric_columns,
    transform_order_items,
    transform_orders,
    transform_products,
    transform_customers,
    transform_sellers,
    transform_payments,
    transform_reviews,
)


def test_clean_column_names_basic():
    df = pd.DataFrame({"Order ID": [1], "Product Name": ["Phone"]})
    result = clean_column_names(df)
    assert "order_id" in result.columns
    assert "product_name" in result.columns


def test_clean_column_names_strips_whitespace():
    df = pd.DataFrame({"  City  ": ["SP"]})
    result = clean_column_names(df)
    assert "city" in result.columns


def test_clean_column_names_does_not_mutate_original():
    df = pd.DataFrame({"Order ID": [1]})
    _ = clean_column_names(df)
    assert "Order ID" in df.columns


def test_coerce_numeric_columns_converts_strings():
    df = pd.DataFrame({"price": ["10.50", "bad", None]})
    result = coerce_numeric_columns(df, ["price"])
    assert result["price"].dtype.kind in "fi"
    assert result["price"].iloc[0] == pytest.approx(10.50)
    assert pd.isna(result["price"].iloc[1])


def test_transform_order_items_deduplicates():
    df = pd.DataFrame({
        "order_id":      ["A", "A"],
        "order_item_id": [1,   1],
        "product_id":    ["P", "P"],
        "seller_id":     ["S", "S"],
        "price":         [100, 100],
        "freight_value": [10,  10],
    })
    result = transform_order_items(df)
    assert len(result) == 1


def test_transform_order_items_numeric_types():
    df = pd.DataFrame({
        "order_id":      ["A"],
        "order_item_id": [1],
        "product_id":    ["P"],
        "seller_id":     ["S"],
        "price":         ["99.99"],
        "freight_value": ["5.00"],
    })
    result = transform_order_items(df)
    assert result["price"].dtype.kind in "fi"
    assert result["freight_value"].dtype.kind in "fi"


def test_transform_orders_parses_datetimes():
    df = pd.DataFrame({
        "order_id":                   ["ORD1"],
        "customer_id":                ["C1"],
        "order_status":               ["delivered"],
        "order_purchase_timestamp":   ["2018-01-01 12:00:00"],
        "order_approved_at":          ["2018-01-01 13:00:00"],
        "order_delivered_carrier_date": [None],
        "order_delivered_customer_date": [None],
        "order_estimated_delivery_date": [None],
    })
    result = transform_orders(df)
    assert pd.api.types.is_datetime64_any_dtype(result["order_purchase_timestamp"])


def test_transform_orders_deduplicates():
    df = pd.DataFrame({
        "order_id":                   ["X", "X"],
        "customer_id":                ["C", "C"],
        "order_status":               ["delivered", "delivered"],
        "order_purchase_timestamp":   ["2018-01-01", "2018-01-01"],
        "order_approved_at":          [None, None],
        "order_delivered_carrier_date": [None, None],
        "order_delivered_customer_date": [None, None],
        "order_estimated_delivery_date": [None, None],
    })
    result = transform_orders(df)
    assert len(result) == 1


def test_transform_customers_deduplicates():
    df = pd.DataFrame({
        "customer_id":        ["C1", "C1"],
        "customer_unique_id": ["U1", "U1"],
        "customer_zip_code_prefix": [12345, 12345],
        "customer_city":      ["SP", "SP"],
        "customer_state":     ["SP", "SP"],
    })
    result = transform_customers(df)
    assert len(result) == 1


def test_transform_sellers_deduplicates():
    df = pd.DataFrame({
        "seller_id":               ["S1", "S1"],
        "seller_zip_code_prefix":  [11000, 11000],
        "seller_city":             ["RJ", "RJ"],
        "seller_state":            ["RJ", "RJ"],
    })
    result = transform_sellers(df)
    assert len(result) == 1


def test_transform_products_renames_typo_columns():
    df = pd.DataFrame({
        "product_id":                  ["P1"],
        "product_category_name":       ["electronics"],
        "product_name_lenght":         [10],
        "product_description_lenght":  [50],
        "product_photos_qty":          [3],
        "product_weight_g":            [200],
        "product_length_cm":           [20],
        "product_height_cm":           [10],
        "product_width_cm":            [15],
    })
    result = transform_products(df)
    assert "product_name_length" in result.columns
    assert "product_description_length" in result.columns


def test_transform_payments_coerces_numerics():
    df = pd.DataFrame({
        "order_id":             ["O1"],
        "payment_sequential":   [1],
        "payment_type":         ["credit_card"],
        "payment_installments": ["3"],
        "payment_value":        ["150.75"],
    })
    result = transform_payments(df)
    assert result["payment_value"].dtype.kind in "fi"
    assert result["payment_installments"].dtype.kind in "fi"


def test_transform_reviews_parses_score():
    df = pd.DataFrame({
        "review_id":               ["R1"],
        "order_id":                ["O1"],
        "review_score":            ["4"],
        "review_comment_title":    [None],
        "review_comment_message":  [None],
        "review_creation_date":    ["2018-06-01"],
        "review_answer_timestamp": ["2018-06-02"],
    })
    result = transform_reviews(df)
    assert result["review_score"].dtype.kind in "fi"
    assert pd.api.types.is_datetime64_any_dtype(result["review_creation_date"])
