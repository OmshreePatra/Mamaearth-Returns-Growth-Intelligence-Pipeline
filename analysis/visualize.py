from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VIS_DIR = BASE_DIR / "visualizations"

VIS_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD RAW DATA
# ============================================================

customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")


# ============================================================
# APPLY SAME CLEANING LOGIC AS clean_and_eda.py
# ============================================================

orders["payment_method"] = (
    orders["payment_method"]
    .str.strip()
    .str.upper()
)

duplicate_subset = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned"
]

duplicate_mask = orders.duplicated(
    subset=duplicate_subset,
    keep="first"
)

orders_clean = orders.loc[~duplicate_mask].copy()

orders_clean["discount_pct"] = (
    orders_clean["discount_pct"].fillna(0)
)

rating_median = orders_clean["rating"].median()

orders_clean["rating"] = (
    orders_clean["rating"].fillna(rating_median)
)


# ============================================================
# MERGE DATA
# ============================================================

merged = orders_clean.merge(
    products,
    on="product_id",
    how="left"
)

merged = merged.merge(
    customers,
    on="customer_id",
    how="left"
)

merged["order_value"] = (
    merged["quantity"]
    * merged["price"]
    * (1 - merged["discount_pct"] / 100)
)


# ============================================================
# OUTLIER FLAG
# ============================================================

Q1 = merged["quantity"].quantile(0.25)
Q3 = merged["quantity"].quantile(0.75)

IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

merged["is_outlier"] = (
    (merged["quantity"] < lower_bound)
    | (merged["quantity"] > upper_bound)
)


# ============================================================
# VISUALIZATION 1 — RETURN RATE BY PAYMENT METHOD
# ============================================================

payment_return_rate = (
    merged
    .groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    payment_return_rate.index,
    payment_return_rate.values
)

plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")
plt.title("COD Returns at 44.4% — 3x Card")

plt.ylim(
    0,
    payment_return_rate.max() + 10
)

for bar, value in zip(
    bars,
    payment_return_rate.values
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{value:.1f}%",
        ha="center"
    )

plt.tight_layout()

return_chart_path = (
    VIS_DIR / "return_rate_by_payment.png"
)

plt.savefig(
    return_chart_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    f"Saved: {return_chart_path}"
)


# ============================================================
# VISUALIZATION 2 — OUTLIER-CORRECTED MONTHLY REVENUE
# ============================================================

merged["order_date"] = pd.to_datetime(
    merged["order_date"]
)

merged["year_month"] = (
    merged["order_date"]
    .dt.to_period("M")
)

monthly_revenue_corrected = (
    merged.loc[~merged["is_outlier"]]
    .groupby("year_month")["order_value"]
    .sum()
)

months = monthly_revenue_corrected.index.astype(str)
revenue = monthly_revenue_corrected.values

plt.figure(figsize=(9, 5))

plt.plot(
    months,
    revenue,
    marker="o"
)

plt.xlabel("Month")
plt.ylabel("Revenue (INR)")
plt.title(
    "Outlier-Corrected Monthly Revenue — March 2026 Peak"
)

plt.xticks(rotation=45)

plt.tight_layout()

monthly_chart_path = (
    VIS_DIR / "monthly_revenue_trend.png"
)

plt.savefig(
    monthly_chart_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    f"Saved: {monthly_chart_path}"
)