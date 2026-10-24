from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.data_loader import RAW_DIR


DATE_COLUMNS = {
    "order_purchase_timestamp": "purchase_ts",
    "order_approved_at": "approved_ts",
    "order_delivered_carrier_date": "carrier_ts",
    "order_delivered_customer_date": "delivered_ts",
    "order_estimated_delivery_date": "estimated_delivery_ts",
    "review_creation_date": "review_created_ts",
}


def parse_datetime_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def normalize_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    renamed = {old: new for old, new in DATE_COLUMNS.items() if old in out.columns}
    out = out.rename(columns=renamed)
    relevant = [c for c in out.columns if "ts" in c.lower() or "date" in c.lower()]
    return parse_datetime_columns(out, relevant)


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = normalize_date_columns(out)
    out["order_id"] = out["order_id"].astype(str)
    out["customer_id"] = out["customer_id"].astype(str)
    out["order_status"] = out["order_status"].fillna("unknown").astype(str)
    if "purchase_ts" in out.columns:
        out["order_year"] = out["purchase_ts"].dt.year
        out["order_month"] = out["purchase_ts"].dt.to_period("M").astype(str)
    else:
        out["order_year"] = None
        out["order_month"] = None
    return out


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["order_id"] = out["order_id"].astype(str)
    out["product_id"] = out["product_id"].astype(str)
    out["seller_id"] = out["seller_id"].fillna("missing").astype(str)
    out["price"] = pd.to_numeric(out["price"], errors="coerce").fillna(0.0)
    out["freight_value"] = pd.to_numeric(out["freight_value"], errors="coerce").fillna(0.0)
    out["item_total_value"] = out["price"] + out["freight_value"]
    return out


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["product_id"] = out["product_id"].astype(str)
    out["product_category_name"] = out["product_category_name"].fillna("unknown").astype(str)
    return out


def clean_category_translation(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["product_category_name"] = out["product_category_name"].fillna("unknown").astype(str)
    out["product_category_name_english"] = out["product_category_name_english"].fillna("Unknown").astype(str)
    return out


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["order_id"] = out["order_id"].astype(str)
    out["review_id"] = out["review_id"].astype(str)
    out["review_score"] = pd.to_numeric(out["review_score"], errors="coerce")
    out = normalize_date_columns(out)
    return out


def clean_dataset() -> dict[str, pd.DataFrame]:
    from src.data_loader import load_csv_table

    orders = clean_orders(load_csv_table("olist_orders_dataset.csv"))
    items = clean_order_items(load_csv_table("olist_order_items_dataset.csv"))
    products = clean_products(load_csv_table("olist_products_dataset.csv"))
    reviews = clean_reviews(load_csv_table("olist_order_reviews_dataset.csv"))
    category_translation = clean_category_translation(load_csv_table("product_category_name_translation.csv"))
    return {
        "orders": orders,
        "items": items,
        "products": products,
        "reviews": reviews,
        "category_translation": category_translation,
    }


def humanize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()
