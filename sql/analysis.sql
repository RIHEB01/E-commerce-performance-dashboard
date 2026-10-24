WITH order_metrics AS (
  SELECT
    o.order_id,
    o.order_status,
    CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_ts,
    CAST(o.order_delivered_customer_date AS TIMESTAMP) AS delivered_ts,
    CAST(o.order_estimated_delivery_date AS TIMESTAMP) AS estimated_delivery_ts
  FROM read_csv_auto('data/raw/olist_orders_dataset.csv') AS o
),
item_metrics AS (
  SELECT
    i.order_id,
    SUM(i.price) AS item_sales_value
  FROM read_csv_auto('data/raw/olist_order_items_dataset.csv') AS i
  GROUP BY i.order_id
)
SELECT
  COUNT(DISTINCT CASE WHEN order_status = 'delivered' THEN order_id END) AS delivered_orders,
  SUM(item_sales_value) AS total_item_sales_value,
  AVG(CASE WHEN order_status = 'delivered' THEN DATE_DIFF('second', purchase_ts, delivered_ts) / 86400.0 END) AS avg_delivery_days,
  AVG(CASE WHEN order_status = 'delivered' AND delivered_ts IS NOT NULL AND estimated_delivery_ts IS NOT NULL THEN CASE WHEN delivered_ts > estimated_delivery_ts THEN 1 ELSE 0 END END) AS late_delivery_rate
FROM order_metrics om
LEFT JOIN item_metrics im ON im.order_id = om.order_id;
