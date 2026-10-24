from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.cleaning import clean_dataset
from src.metrics import (
    average_order_value,
    average_review_score,
    build_order_metrics,
    build_product_category_summary,
    compute_delivery_stats,
    compute_monthly_sales,
    distinct_delivered_orders,
    item_sales_value,
    on_time_delivery_rate,
)
from src.sql_analysis import get_sql_snapshot

st.set_page_config(page_title="E-commerce Performance Dashboard", page_icon="📦", layout="wide")


@st.cache_data
def load_dashboard_data():
    data = clean_dataset()
    return data


@st.cache_data
def load_sql_summary():
    return get_sql_snapshot()


def format_currency(value: float) -> str:
    return f"R$ {value:,.2f}"


def show_missing_data_message() -> None:
    st.warning(
        "The dataset is not available locally yet. Download the Olist CSV files from Kaggle and place them in data/raw/ before running the dashboard."
    )


def set_dashboard_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background-color: #f5f7fb; color: #102a43; }
        h1 { font-size: clamp(1.9rem, 3.5vw, 3rem) !important; line-height: 1.1 !important; }
        div[data-testid="stMetricValue"] { font-size: 1.5rem; }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe4ee;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(16, 42, 67, 0.05);
        }
        div[data-testid="stMetric"] p,
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: #102a43 !important;
        }
        .block-container { padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def filter_by_category(orders: pd.DataFrame, items: pd.DataFrame, products: pd.DataFrame, category_translation: pd.DataFrame, selected_categories: list[str]) -> pd.DataFrame:
    if not selected_categories:
        return orders.iloc[0:0].copy()
    category_lookup = category_translation.loc[
        category_translation["product_category_name_english"].isin(selected_categories),
        ["product_category_name", "product_category_name_english"],
    ]
    product_names = category_lookup["product_category_name"].tolist()
    product_ids = products.loc[products["product_category_name"].isin(product_names), "product_id"].unique()
    eligible_order_ids = items.loc[items["product_id"].isin(product_ids), "order_id"].unique()
    return orders.loc[orders["order_id"].isin(eligible_order_ids)].copy()


def build_review_delay_summary(orders: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    review_orders = reviews.loc[reviews["order_id"].isin(orders["order_id"]), ["order_id", "review_score"]].copy()
    order_metrics = build_order_metrics(orders)
    merged = review_orders.merge(
        order_metrics[["order_id", "delivery_duration_days", "late_delivery"]], on="order_id", how="left"
    )
    merged["delay_band"] = pd.cut(
        merged["delivery_duration_days"],
        bins=[-1, 3, 7, 14, 30, 1000],
        labels=["0-3 days", "4-7 days", "8-14 days", "15-30 days", "30+ days"],
        right=False,
    )
    return merged.groupby("delay_band", as_index=False)["review_score"].mean().rename(columns={"review_score": "avg_review_score"})


def main() -> None:
    set_dashboard_theme()
    st.title("E-commerce Performance Dashboard")
    st.caption("Brazilian marketplace order and delivery analytics for operational reporting and business decision support.")

    try:
        data = load_dashboard_data()
    except FileNotFoundError:
        show_missing_data_message()
        return

    orders = data["orders"]
    items = data["items"]
    products = data["products"]
    reviews = data["reviews"]
    category_translation = data["category_translation"]

    if orders.empty:
        st.info("No data was loaded. Add the Olist CSV files to data/raw and restart the app.")
        return

    order_metrics = build_order_metrics(orders)
    sql_summary = load_sql_summary()
    date_min = orders["purchase_ts"].min().strftime("%Y-%m-%d") if orders["purchase_ts"].notna().any() else "N/A"
    date_max = orders["purchase_ts"].max().strftime("%Y-%m-%d") if orders["purchase_ts"].notna().any() else "N/A"

    with st.sidebar:
        st.header("Filters")
        status_options = sorted(orders["order_status"].dropna().unique())
        category_options = sorted(category_translation["product_category_name_english"].dropna().unique())
        selected_statuses = st.multiselect("Order status", options=status_options, default=status_options)
        selected_categories = st.multiselect("Product category", options=category_options, default=category_options)
        if orders["purchase_ts"].notna().any():
            date_range = st.date_input(
                "Purchase date range",
                value=(orders["purchase_ts"].min().date(), orders["purchase_ts"].max().date()),
                min_value=orders["purchase_ts"].min().date(),
                max_value=orders["purchase_ts"].max().date(),
            )
        else:
            date_range = None

    if date_range is not None:
        start_date, end_date = date_range
        filtered_orders = order_metrics.loc[
            order_metrics["purchase_ts"].between(pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1))
        ].copy()
    else:
        filtered_orders = order_metrics.copy()

    filtered_orders = filtered_orders.loc[filtered_orders["order_status"].isin(selected_statuses)].copy()
    filtered_orders = filter_by_category(filtered_orders, items, products, category_translation, selected_categories)

    filtered_items = items.loc[items["order_id"].isin(filtered_orders["order_id"].unique())].copy()
    filtered_reviews = reviews.loc[reviews["order_id"].isin(filtered_orders["order_id"].unique())].copy()

    item_value = item_sales_value(filtered_items)
    delivered_orders = distinct_delivered_orders(filtered_orders)
    aov = average_order_value(filtered_orders, filtered_items)
    on_time_rate = on_time_delivery_rate(filtered_orders)
    avg_review = average_review_score(filtered_reviews)
    avg_delivery_days = filtered_orders.loc[filtered_orders["order_status"].eq("delivered"), "delivery_duration_days"].mean()
    late_ratio = filtered_orders.loc[filtered_orders["order_status"].eq("delivered"), "late_delivery"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Delivered orders", f"{delivered_orders:,}", help="Distinct orders with delivered status in the filtered population.")
    col2.metric("Item sales value", format_currency(item_value), help="Sum of item prices; excludes freight and is not company revenue or profit.")
    col3.metric("Average order value", format_currency(aov), help="Item prices for delivered orders divided by distinct delivered orders; freight is excluded.")
    col4.metric("On-time delivery rate", f"{on_time_rate * 100:.1f}%", help="Eligible delivered orders not late divided by delivered orders with valid delivery and estimate timestamps.")
    col5.metric("Average review score", f"{avg_review:.2f}/5", help="Mean of valid review scores in the filtered order population.")
    st.caption(f"Data period: {date_min} to {date_max} · Source: Olist Brazilian E-Commerce Public Dataset (Kaggle) · Historical marketplace data.")

    st.subheader("Overview")
    st.caption("The KPI cards use the selected date range, status, and category filters. Missing timestamps are excluded only where a metric requires a valid date value.")

    monthly = compute_monthly_sales(filtered_items, filtered_orders)
    if not monthly.empty:
        trend_fig = px.line(monthly, x="order_month", y="item_sales_value", markers=True)
        trend_fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), title="Monthly item sales value")
        st.plotly_chart(trend_fig, width="stretch")

    category_summary = build_product_category_summary(filtered_items, products, category_translation)
    if not category_summary.empty:
        category_fig = px.bar(
            category_summary.head(8),
            x="category_label",
            y="item_sales_value",
            text_auto=".2s",
            color_discrete_sequence=["#1f77b4"],
        )
        category_fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), title="Top product categories by item sales value")
        st.plotly_chart(category_fig, width="stretch")

    st.header("Delivery")
    delivery_stats = compute_delivery_stats(filtered_orders)
    if not delivery_stats.empty:
        delivery_fig = px.line(delivery_stats, x="order_month", y="avg_delivery_days", markers=True)
        delivery_fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), title="Average delivery duration by month")
        st.plotly_chart(delivery_fig, width="stretch")

    late_fig = px.bar(
        delivery_stats,
        x="order_month",
        y="late_rate",
        labels={"late_rate": "Late delivery rate", "order_month": "Month"},
        color_discrete_sequence=["#ff7f0e"],
    )
    late_fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), title="Late-delivery rate by month")
    st.plotly_chart(late_fig, width="stretch")

    st.header("Customer experience")
    if not filtered_reviews.empty:
        review_scores = filtered_reviews["review_score"].value_counts().sort_index().rename_axis("score").reset_index(name="count")
        review_fig = px.bar(review_scores, x="score", y="count", color="score", color_continuous_scale="Viridis")
        review_fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), title="Review score distribution")
        st.plotly_chart(review_fig, width="stretch")

        review_delay = build_review_delay_summary(filtered_orders, filtered_reviews)
        if not review_delay.empty:
            delay_fig = px.line(review_delay, x="delay_band", y="avg_review_score", markers=True)
            delay_fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), title="Average review score by delivery delay band")
            st.plotly_chart(delay_fig, width="stretch")
            st.caption("Association between delay and review score does not establish causation.")

    st.header("Data quality and definitions")
    st.markdown(
        "- Selected date range: based on order purchase timestamp and filtered by the chosen order status and category selections.\n"
        "- Excluded records: orders without valid purchase or delivery timestamps are excluded from delivery-duration metrics when the calculation requires a date value. Review rows without a valid score are excluded from the average review score denominator.\n"
        "- KPI definitions: Delivered orders = distinct `order_id` rows with `order_status = 'delivered'`; Item sales value = sum of `price` for the filtered order-item population; Average order value = item sales value divided by distinct eligible delivered orders; Delivery duration = `order_delivered_customer_date - order_purchase_timestamp` in days; Estimated delivery duration = `order_estimated_delivery_date - order_purchase_timestamp` in days; Late delivery = delivered timestamp later than estimated delivery timestamp; On-time delivery rate = eligible delivered orders not late divided by eligible delivered orders with valid timestamps; Average review score = mean of valid review rows.\n"
        "- Known limitations: the dataset is historical public marketplace data, not a current company dataset; correlation between delivery delay and review score is not proof of causation; some orders have missing timestamps or incomplete metadata."
    )

    with st.expander("SQL validation snapshot"):
        st.write(f"DuckDB snapshot: {sql_summary['delivered_orders']:,} delivered orders; item sales value {format_currency(float(sql_summary['item_sales_value']))}; on-time rate {float(sql_summary['on_time_delivery_rate']):.2%}; avg review {float(sql_summary['avg_review_score']):.2f}/5.")

    with st.expander("Dataset notes"):
        st.write(f"Orders loaded: {len(orders):,}")
        st.write(f"Order items loaded: {len(items):,}")
        st.write(f"Reviews loaded: {len(reviews):,}")
        st.write(f"Average delivery duration: {avg_delivery_days:.2f} days")
        st.write(f"Late-delivery share among delivered orders: {late_ratio * 100:.1f}%")


if __name__ == "__main__":
    main()
