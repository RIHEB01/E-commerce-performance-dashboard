import pandas as pd

from src.metrics import (
    average_order_value,
    build_order_metrics,
    compute_monthly_sales,
    distinct_delivered_orders,
    item_sales_value,
    on_time_delivery_rate,
)


def test_distinct_delivered_orders():
    orders = pd.DataFrame(
        {
            "order_id": ["a", "b", "c"],
            "order_status": ["delivered", "delivered", "shipped"],
            "purchase_ts": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "delivered_ts": pd.to_datetime(["2024-01-05", "2024-01-06", "NaT"]),
            "estimated_delivery_ts": pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-04"]),
        }
    )
    assert distinct_delivered_orders(orders) == 2


def test_item_sales_value():
    items = pd.DataFrame({"price": [10.5, 20.0, 30.0]})
    assert item_sales_value(items) == 60.5


def test_average_order_value_and_on_time_rate():
    orders = pd.DataFrame(
        {
            "order_id": ["a", "b"],
            "order_status": ["delivered", "delivered"],
            "purchase_ts": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "delivered_ts": pd.to_datetime(["2024-01-04", "2024-01-05"]),
            "estimated_delivery_ts": pd.to_datetime(["2024-01-04", "2024-01-03"]),
        }
    )
    orders = build_order_metrics(orders)
    items = pd.DataFrame({"order_id": ["a", "b"], "price": [100.0, 200.0]})
    assert average_order_value(orders, items) == 150.0
    assert on_time_delivery_rate(orders) == 0.5


def test_missing_delivery_timestamps_are_excluded_from_on_time_denominator():
    orders = pd.DataFrame(
        {
            "order_id": ["on-time", "late", "unknown"],
            "order_status": ["delivered", "delivered", "delivered"],
            "purchase_ts": pd.to_datetime(["2024-01-01"] * 3),
            "delivered_ts": pd.to_datetime(["2024-01-03", "2024-01-05", None]),
            "estimated_delivery_ts": pd.to_datetime(["2024-01-03", "2024-01-04", "2024-01-04"]),
        }
    )
    metrics = build_order_metrics(orders)
    assert on_time_delivery_rate(metrics) == 0.5
    assert metrics["delivery_eligible"].sum() == 2


def test_monthly_delivered_orders_are_not_inflated_by_item_rows():
    orders = pd.DataFrame(
        {
            "order_id": ["a", "b"],
            "order_status": ["delivered", "shipped"],
            "order_month": ["2024-01", "2024-01"],
        }
    )
    items = pd.DataFrame(
        {
            "order_id": ["a", "a", "b"],
            "price": [10.0, 20.0, 30.0],
        }
    )
    monthly = compute_monthly_sales(items, orders)
    assert monthly.loc[0, "item_sales_value"] == 60.0
    assert monthly.loc[0, "delivered_orders"] == 1
