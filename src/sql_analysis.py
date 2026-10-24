from __future__ import annotations

from pathlib import Path

import duckdb


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"


def get_sql_snapshot() -> dict[str, float | int]:
    conn = duckdb.connect(database=":memory:")
    query = """
    WITH orders AS (
        SELECT
            order_id,
            order_status,
            CAST(order_purchase_timestamp AS TIMESTAMP) AS purchase_ts,
            CAST(order_delivered_customer_date AS TIMESTAMP) AS delivered_ts,
            CAST(order_estimated_delivery_date AS TIMESTAMP) AS estimated_delivery_ts
        FROM read_csv_auto('data/raw/olist_orders_dataset.csv', header=true)
    ),
    items AS (
        SELECT
            order_id,
            CAST(price AS DOUBLE) AS price
        FROM read_csv_auto('data/raw/olist_order_items_dataset.csv', header=true)
    ),
    reviews AS (
        SELECT
            order_id,
            CAST(review_score AS DOUBLE) AS review_score
        FROM read_csv_auto('data/raw/olist_order_reviews_dataset.csv', header=true)
    )
    SELECT
        (SELECT COUNT(DISTINCT order_id) FROM orders WHERE order_status = 'delivered') AS delivered_orders,
        (SELECT SUM(price) FROM items) AS item_sales_value,
        (
            SELECT AVG(CASE WHEN delivered_ts IS NOT NULL AND estimated_delivery_ts IS NOT NULL THEN CASE WHEN delivered_ts <= estimated_delivery_ts THEN 1.0 ELSE 0.0 END END)
            FROM orders
            WHERE order_status = 'delivered'
        ) AS on_time_delivery_rate,
        (
            SELECT AVG(CASE WHEN delivered_ts IS NOT NULL AND purchase_ts IS NOT NULL THEN DATE_DIFF('second', purchase_ts, delivered_ts) / 86400.0 END)
            FROM orders
            WHERE order_status = 'delivered'
        ) AS avg_delivery_days,
        (
            SELECT AVG(review_score)
            FROM reviews
            WHERE review_score IS NOT NULL
        ) AS avg_review_score
    """
    result = conn.execute(query).fetchone()
    columns = [
        "delivered_orders",
        "item_sales_value",
        "on_time_delivery_rate",
        "avg_delivery_days",
        "avg_review_score",
    ]
    return {column: value for column, value in zip(columns, result)}
