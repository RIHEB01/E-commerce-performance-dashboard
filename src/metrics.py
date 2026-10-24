from __future__ import annotations

from typing import Any

import pandas as pd


def distinct_delivered_orders(orders: pd.DataFrame) -> int:
    if orders.empty:
        return 0
    return int(orders.loc[orders["order_status"].eq("delivered"), "order_id"].nunique())


def item_sales_value(items: pd.DataFrame) -> float:
    if items.empty:
        return 0.0
    return float(items["price"].sum())


def average_order_value(orders: pd.DataFrame, items: pd.DataFrame) -> float:
    eligible_orders = orders.loc[orders["order_status"].eq("delivered"), "order_id"].dropna().unique()
    if len(eligible_orders) == 0:
        return 0.0
    order_item_value = items.loc[items["order_id"].isin(eligible_orders), "price"].sum()
    return float(order_item_value / len(eligible_orders))


def delivery_duration_days(order_row: pd.Series) -> float | None:
    purchase_ts = order_row.get("purchase_ts")
    delivered_ts = order_row.get("delivered_ts")
    if pd.isna(purchase_ts) or pd.isna(delivered_ts):
        return None
    return (delivered_ts - purchase_ts).total_seconds() / 86400


def estimated_delivery_duration_days(order_row: pd.Series) -> float | None:
    purchase_ts = order_row.get("purchase_ts")
    estimated_ts = order_row.get("estimated_delivery_ts")
    if pd.isna(purchase_ts) or pd.isna(estimated_ts):
        return None
    return (estimated_ts - purchase_ts).total_seconds() / 86400


def build_order_metrics(orders: pd.DataFrame) -> pd.DataFrame:
    out = orders.copy()
    out["delivery_duration_days"] = (
        out["delivered_ts"] - out["purchase_ts"]
    ).dt.total_seconds() / 86400
    out["estimated_delivery_days"] = (
        out["estimated_delivery_ts"] - out["purchase_ts"]
    ).dt.total_seconds() / 86400
    delivery_eligible = out["delivered_ts"].notna() & out["estimated_delivery_ts"].notna()
    out["delivery_eligible"] = delivery_eligible
    out["late_delivery"] = out["delivered_ts"].gt(out["estimated_delivery_ts"]).astype("boolean")
    out.loc[~delivery_eligible, "late_delivery"] = pd.NA
    return out


def on_time_delivery_rate(orders: pd.DataFrame) -> float:
    eligible = orders.loc[orders["order_status"].eq("delivered")].copy()
    if eligible.empty:
        return 0.0
    eligible = eligible.dropna(subset=["delivered_ts", "estimated_delivery_ts"])
    if eligible.empty:
        return 0.0
    on_time = eligible.loc[~eligible["late_delivery"].fillna(False), "order_id"].nunique()
    total = eligible["order_id"].nunique()
    if total == 0:
        return 0.0
    return float(on_time / total)


def average_review_score(reviews: pd.DataFrame) -> float:
    valid = reviews.loc[reviews["review_score"].notna(), "review_score"]
    if valid.empty:
        return 0.0
    return float(valid.mean())


def compute_monthly_sales(items: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    if items.empty or orders.empty:
        return pd.DataFrame(columns=["order_month", "item_sales_value", "delivered_orders"])
    order_month = orders[["order_id", "order_month"]].drop_duplicates("order_id")
    order_items = items[["order_id", "price"]].merge(order_month, on="order_id", how="inner")
    monthly_sales = order_items.groupby("order_month", as_index=False).agg(
        item_sales_value=("price", "sum")
    )
    monthly_delivered = (
        orders.loc[orders["order_status"].eq("delivered")]
        .groupby("order_month", as_index=False)
        .agg(delivered_orders=("order_id", "nunique"))
    )
    return monthly_sales.merge(monthly_delivered, on="order_month", how="left").fillna(
        {"delivered_orders": 0}
    ).sort_values("order_month")


def build_product_category_summary(items: pd.DataFrame, products: pd.DataFrame, category_translation: pd.DataFrame) -> pd.DataFrame:
    item_value = items[["order_id", "product_id", "price"]].merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
    translated = item_value.merge(category_translation[["product_category_name", "product_category_name_english"]], on="product_category_name", how="left")
    category_name = translated["product_category_name_english"].fillna(translated["product_category_name"])
    translated["category_label"] = category_name
    return (
        translated.groupby("category_label", as_index=False)
        .agg(item_sales_value=("price", "sum"))
        .sort_values("item_sales_value", ascending=False)
    )


def compute_delivery_stats(orders: pd.DataFrame) -> pd.DataFrame:
    order_metrics = build_order_metrics(orders)
    delivery_stats = order_metrics.loc[
        order_metrics["order_status"].eq("delivered") & order_metrics["delivered_ts"].notna()
    ].copy()
    if delivery_stats.empty:
        return pd.DataFrame(columns=["order_month", "avg_delivery_days", "late_rate"])
    delivery_stats["order_month"] = delivery_stats["purchase_ts"].dt.to_period("M").astype(str)
    summary = delivery_stats.groupby("order_month", as_index=False).agg(
        avg_delivery_days=("delivery_duration_days", "mean"),
        late_rate=("late_delivery", "mean"),
    )
    return summary.sort_values("order_month")


def validate_kpis(orders: pd.DataFrame, items: pd.DataFrame, reviews: pd.DataFrame) -> dict[str, Any]:
    order_metrics = build_order_metrics(orders)
    delivered_orders = distinct_delivered_orders(order_metrics)
    item_value = item_sales_value(items)
    avg_order_value = average_order_value(order_metrics, items)
    on_time_rate = on_time_delivery_rate(order_metrics)
    avg_review = average_review_score(reviews)
    return {
        "delivered_orders": delivered_orders,
        "item_sales_value": item_value,
        "average_order_value": avg_order_value,
        "on_time_delivery_rate": on_time_rate,
        "average_review_score": avg_review,
    }
