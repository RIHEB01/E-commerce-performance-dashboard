# E-commerce Performance Dashboard

## Project overview

This project is a local-first e-commerce analytics dashboard built to explore Brazilian marketplace performance using the Olist public dataset. It is designed to show practical skills in data cleaning, KPI definition, SQL analysis, dashboard design, and reporting for junior data analyst, BI analyst, and reporting analyst roles.

The dashboard is based on historical public marketplace data and is intended for professional analytical review, not for making claims about a live company. It focuses on honest, explainable analysis and clear documentation of limitations.

## What this project is good for

- Building a professional analytics case study
- Demonstrating Python, pandas, SQL, and dashboard work on real data
- Practicing KPI definition and business-safe metric communication
- Showing clearly how a data project moves from raw files to polished reporting
- Creating a foundation for future work in BI, analytics, or data science

## Repository structure

```text
ecommerce-performance-dashboard/
  app.py
  README.md
  requirements.txt
  .gitignore
  LICENSE
  data/
    raw/
      .gitkeep
    processed/
      .gitkeep
  sql/
    analysis.sql
  src/
    __init__.py
    cleaning.py
    data_loader.py
    metrics.py
    sql_analysis.py
  tests/
    test_metrics.py
  reports/
  figures/
    .gitkeep
```

## Business questions

1. How are orders and sales changing over time?
2. Which product categories contribute most to item sales?
3. How long do deliveries take, and how often are orders delivered late?
4. How are delivery delays associated with customer review scores?
5. What should a retail or marketplace operations manager investigate next?

## Dataset source and attribution

This project uses the Olist Brazilian E-Commerce Public Dataset from Kaggle.

- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- Dataset license shown on Kaggle: CC BY-NC-SA 4.0. Review the current terms and obtain permission before redistributing the dataset or publicly sharing derived findings or figures. This repository does not include the dataset or data-derived results.
- Important: The raw dataset is not committed to GitHub and should remain local only.

## Local setup

### Windows PowerShell

```powershell
cd "C:\Users\weber\OneDrive\Desktop\Ecommerce performance dashboard"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
cd "/path/to/Ecommerce performance dashboard"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Data download and placement

1. Download the Olist dataset from Kaggle.
2. Place the CSV files in `data/raw/`.
3. Keep the files local and do not commit them to GitHub.
4. Required files for this project include:
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_products_dataset.csv`
   - `olist_order_reviews_dataset.csv`
   - `product_category_name_translation.csv`

## Run the dashboard locally

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Tools used

- Python 3.11+
- pandas
- DuckDB
- Streamlit
- Plotly
- pytest
- Git and GitHub

## Data model and grain

The project uses the following core tables:

- `orders`: one row per order; this is the main grain for order-level metrics
- `order_items`: one row per item in an order; this is the item-level grain used for item sales analysis
- `products`: product metadata used to map products to categories
- `reviews`: one row per review; used for review-score analysis
- `product_category_name_translation`: category mapping used for readable labels

Important: order-item rows must not be treated as equivalent to order rows when calculating order-level KPIs. The analysis keeps the grain separate to prevent double-counting and misleading denominators.

## KPI definitions

- Delivered orders: distinct `order_id` values where `order_status = 'delivered'`
- Item sales value: sum of `price` values for the selected population. This is not company revenue or profit.
- Average order value: sum of item prices for eligible delivered orders divided by the distinct eligible delivered order count; freight is excluded. This numerator can differ from the Item sales value card when the selected population includes non-delivered orders.
- Delivery duration: `order_delivered_customer_date - order_purchase_timestamp`, measured in days
- Estimated delivery duration: `order_estimated_delivery_date - order_purchase_timestamp`, measured in days
- Late delivery: a delivered order where the delivered timestamp is later than the estimated delivery timestamp
- On-time delivery rate: eligible delivered orders that were not late divided by eligible delivered orders with valid timestamps
- Average review score: mean of valid review scores in the selected population; the denominator is valid review rows, not total order count

## Cleaning and validation steps

- Inspect columns, date ranges, nulls, and duplicate keys before analysis
- Standardize timestamp columns and document missing values
- Keep item-level and order-level tables separate during aggregation
- Reconcile major totals and validate joins before reporting numbers
- Use filters only when they preserve valid denominators and clear comparisons

## Results

Data-derived findings and figures are intentionally not included in this public repository while the dataset's licensing implications are being clarified. After downloading the dataset locally and placing the required files in `data/raw/`, run the dashboard to explore the metrics. Do not redistribute the dataset or publish derived results unless the applicable terms permit it.

## Limitations

- The dataset is historical public marketplace data, not a live company dataset.
- Customer review scores can correlate with delivery performance, but this does not prove direct causation.
- Some orders and timestamps may be missing or incomplete, which affects delivery and review calculations.
- The dashboard is intentionally local-first and does not upload or centralize the data elsewhere.

## Additional data that would help next

To continue the analysis beyond this current version, the next step would be to add:
- seller-level performance data
- shipping carrier and route detail
- geography and delivery region data
- product inventory and stock-out information
- marketing or promotion data for the highest-volume periods

## Future improvements

- Add richer SQL validation queries for delivery quality and category segmentation
- Add region, seller, and carrier drill-down filters
- Add saved KPI definitions for dashboard documentation
- Expand the project to forecasting or predictive business analysis

## Dashboard preview

No data-derived dashboard screenshot is included. Add a screenshot only after confirming the applicable dataset terms permit sharing the displayed results.

## Author

**Riheb Gattal**

GitHub: [riheb01](https://github.com/riheb01)

## GitHub publication checklist

Before publishing to GitHub:

- Confirm no raw Kaggle CSV files are included in the repo
- Confirm no `.env`, credentials, or personal data are present
- Confirm the README is the final version and the findings are evidence-based
- Confirm the dashboard runs locally after install
- Confirm the repository snapshot is ready for a public audience

## Security and privacy

- Keep the project local-first and do not upload data or credentials to external services
- Do not commit Kaggle passwords, API tokens, or personal data
- Add local data, caches, environments, and generated outputs to `.gitignore`
- Validate file paths and handle missing inputs with clear messages
- Before publishing, check that no dataset or secret is included in the final repository snapshot
