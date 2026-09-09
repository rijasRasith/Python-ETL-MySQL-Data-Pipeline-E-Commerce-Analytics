import pandas as pd
import pytest

from src.validate import (
    validate_customers,
    validate_orders,
    validate_order_items,
    validate_payments,
    validate_products,
    validate_reviews,
)


def _make_customers(**overrides):
    base = {
        "customer_id":             ["C1"],
        "customer_unique_id":      ["U1"],
        "customer_zip_code_prefix": [12345],
        "customer_city":           ["SP"],
        "customer_state":          ["SP"],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _make_orders(**overrides):
    base = {
        "order_id":                 ["O1"],
        "customer_id":              ["C1"],
        "order_status":             ["delivered"],
        "order_purchase_timestamp": [pd.Timestamp("2018-01-01")],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _make_order_items(**overrides):
    base = {
        "order_id":      ["O1"],
        "order_item_id": [1],
        "product_id":    ["P1"],
        "seller_id":     ["S1"],
        "price":         [100.0],
        "freight_value": [10.0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _make_payments(**overrides):
    base = {
        "order_id":             ["O1"],
        "payment_sequential":   [1],
        "payment_type":         ["credit_card"],
        "payment_installments": [1],
        "payment_value":        [110.0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _make_reviews(**overrides):
    base = {
        "review_id":    ["R1"],
        "order_id":     ["O1"],
        "review_score": [5],
    }
    base.update(overrides)
    return pd.DataFrame(base)


class TestValidateCustomers:

    def test_passes_valid_data(self):
        df = _make_customers()
        validate_customers(df)

    def test_raises_on_missing_column(self):
        df = pd.DataFrame({"customer_id": ["C1"]})
        with pytest.raises(ValueError, match="customer_unique_id"):
            validate_customers(df)

    def test_raises_on_null_customer_id(self):
        df = _make_customers(customer_id=[None])
        with pytest.raises(ValueError, match="null customer_id"):
            validate_customers(df)

    def test_raises_on_null_unique_id(self):
        df = _make_customers(customer_unique_id=[None])
        with pytest.raises(ValueError, match="null customer_unique_id"):
            validate_customers(df)


class TestValidateOrders:

    def test_passes_valid_data(self):
        df = _make_orders()
        validate_orders(df)

    def test_raises_on_missing_column(self):
        df = pd.DataFrame({"order_id": ["O1"]})
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_orders(df)

    def test_raises_on_null_order_id(self):
        df = _make_orders(order_id=[None])
        with pytest.raises(ValueError, match="null order_id"):
            validate_orders(df)

    def test_raises_on_duplicate_order_id(self):
        df = pd.concat([_make_orders(), _make_orders()], ignore_index=True)
        with pytest.raises(ValueError, match="duplicate order_id"):
            validate_orders(df)

    def test_raises_on_null_customer_id(self):
        df = _make_orders(customer_id=[None])
        with pytest.raises(ValueError, match="null customer_id"):
            validate_orders(df)


class TestValidateOrderItems:

    def test_passes_valid_data(self):
        df = _make_order_items()
        valid, rejected = validate_order_items(df)
        assert len(valid) == 1
        assert len(rejected) == 0

    def test_rejects_negative_price(self):
        df = _make_order_items(price=[-5.0])
        valid, rejected = validate_order_items(df)
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_rejects_negative_freight(self):
        df = _make_order_items(freight_value=[-1.0])
        valid, rejected = validate_order_items(df)
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_raises_on_missing_column(self):
        df = pd.DataFrame({"order_id": ["O1"]})
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_order_items(df)


class TestValidatePayments:

    def test_passes_valid_data(self):
        df = _make_payments()
        valid, rejected = validate_payments(df)
        assert len(valid) == 1
        assert len(rejected) == 0

    def test_rejects_negative_payment_value(self):
        df = _make_payments(payment_value=[-10.0])
        valid, rejected = validate_payments(df)
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_rejects_negative_installments(self):
        df = _make_payments(payment_installments=[-1])
        valid, rejected = validate_payments(df)
        assert len(valid) == 0
        assert len(rejected) == 1


class TestValidateProducts:

    def test_passes_valid_data(self):
        df = pd.DataFrame({"product_id": ["P1"]})
        validate_products(df)

    def test_raises_on_null_product_id(self):
        df = pd.DataFrame({"product_id": [None]})
        with pytest.raises(ValueError, match="null product_id"):
            validate_products(df)

    def test_raises_on_duplicate_product_id(self):
        df = pd.DataFrame({"product_id": ["P1", "P1"]})
        with pytest.raises(ValueError, match="duplicate product_id"):
            validate_products(df)


class TestValidateReviews:

    def test_passes_valid_score(self):
        df = _make_reviews(review_score=[5])
        valid, rejected = validate_reviews(df)
        assert len(valid) == 1
        assert len(rejected) == 0

    def test_rejects_score_above_5(self):
        df = _make_reviews(review_score=[6])
        valid, rejected = validate_reviews(df)
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_rejects_score_below_1(self):
        df = _make_reviews(review_score=[0])
        valid, rejected = validate_reviews(df)
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_rejects_null_score(self):
        df = _make_reviews(review_score=[None])
        valid, rejected = validate_reviews(df)
        assert len(valid) == 0
        assert len(rejected) == 1
