import pandas as pd
from pathlib import Path


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# ============================================================
# TASK 1 — LOAD AND INSPECT DATA
# ============================================================

customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")


print("=" * 60)
print("TASK 1 — LOAD AND INSPECT DATA")
print("=" * 60)

print("\nCustomers shape:", customers.shape)
print("Products shape :", products.shape)
print("Orders shape   :", orders.shape)

print("\nOrders columns:")
print(orders.columns.tolist())

print("\nMissing values in orders:")
print(orders.isnull().sum())


# ============================================================
# TASK 2 — STANDARDIZE PAYMENT METHOD CASING
# ============================================================

print("\n" + "=" * 60)
print("TASK 2 — STANDARDIZE PAYMENT METHOD")
print("=" * 60)

print("\nRaw payment_method values:")
print(orders["payment_method"].unique())

print("\nRaw payment_method count:")
print(orders["payment_method"].nunique())


orders["payment_method"] = (
    orders["payment_method"]
    .str.strip()
    .str.upper()
)


print("\nCleaned payment_method values:")
print(orders["payment_method"].unique())

print("\nCleaned payment_method counts:")
print(orders["payment_method"].value_counts())

# ============================================================
# TASK 3 — DETECT AND REMOVE DUPLICATE ORDERS
# ============================================================

print("\n" + "=" * 60)
print("TASK 3 — DETECT AND REMOVE DUPLICATE ORDERS")
print("=" * 60)

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

duplicate_orders = orders.loc[duplicate_mask]

print("\nNumber of duplicate orders detected:")
print(duplicate_mask.sum())

print("\nDuplicate order IDs:")
print(duplicate_orders["order_id"].tolist())

orders_clean = orders.loc[~duplicate_mask].copy()

print("\nShape after removing duplicates:")
print(orders_clean.shape)

# ============================================================
# TASK 4 — IMPUTE MISSING VALUES
# ============================================================

print("\n" + "=" * 60)
print("TASK 4 — IMPUTE MISSING VALUES")
print("=" * 60)

# Count missing values before filling
missing_discount_before = orders_clean["discount_pct"].isna().sum()
missing_rating_before = orders_clean["rating"].isna().sum()

print("\nMissing discount_pct before imputation:")
print(missing_discount_before)

print("\nMissing rating before imputation:")
print(missing_rating_before)


# ------------------------------------------------------------
# discount_pct:
# Business rule -> missing discount means no discount applied
# ------------------------------------------------------------

orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)


# ------------------------------------------------------------
# rating:
# Fill missing values using median of non-null ratings
# ------------------------------------------------------------

rating_median = orders_clean["rating"].median()

print("\nMedian rating before imputation:")
print(rating_median)

orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)


# ------------------------------------------------------------
# Verify missing values after imputation
# ------------------------------------------------------------

print("\nMissing values after imputation:")
print(
    orders_clean[
        ["discount_pct", "rating"]
    ].isnull().sum()
)

# ============================================================
# TASK 5 — MERGE DATA AND RECONCILE REVENUE
# ============================================================

print("\n" + "=" * 60)
print("TASK 5 — MERGE DATA AND RECONCILE REVENUE")
print("=" * 60)

# Merge cleaned orders with products
merged = orders_clean.merge(
    products,
    on="product_id",
    how="left"
)

# Merge with customers
merged = merged.merge(
    customers,
    on="customer_id",
    how="left"
)

# Calculate order value
merged["order_value"] = (
    merged["quantity"]
    * merged["price"]
    * (1 - merged["discount_pct"] / 100)
)

cleaned_total_revenue = merged["order_value"].sum()

print("\nCleaned total revenue:")
print(round(cleaned_total_revenue, 2))


# ------------------------------------------------------------
# Reconciliation with Part 1 raw SQL revenue
# ------------------------------------------------------------

raw_total_revenue = 99860.20

reconciliation_delta = raw_total_revenue - cleaned_total_revenue

print("\nRaw SQL total revenue:")
print(round(raw_total_revenue, 2))

print("\nRevenue difference:")
print(round(reconciliation_delta, 2))


# ------------------------------------------------------------
# Independently calculate value of the 5 dropped duplicates
# ------------------------------------------------------------

duplicate_check = duplicate_orders.merge(
    products,
    on="product_id",
    how="left"
)

duplicate_check["discount_pct"] = (
    duplicate_check["discount_pct"].fillna(0)
)

duplicate_check["order_value"] = (
    duplicate_check["quantity"]
    * duplicate_check["price"]
    * (1 - duplicate_check["discount_pct"] / 100)
)

duplicate_revenue = duplicate_check["order_value"].sum()

print("\nRevenue contributed by removed duplicate orders:")
print(round(duplicate_revenue, 2))


print("\nReconciliation note:")
print(
    f"The raw SQL revenue is ₹{raw_total_revenue:,.2f}, while the cleaned "
    f"revenue is ₹{cleaned_total_revenue:,.2f}. "
    f"The exact difference of ₹{reconciliation_delta:,.2f} is caused by "
    f"the five duplicate orders removed during cleaning. "
    f"The combined order value of those duplicates is ₹{duplicate_revenue:,.2f}. "
    f"Discount and rating imputation did not change the revenue total."
)

# ============================================================
# TASK 6 — IQR OUTLIER DETECTION ON QUANTITY
# ============================================================

print("\n" + "=" * 60)
print("TASK 6 — IQR OUTLIER DETECTION ON QUANTITY")
print("=" * 60)

Q1 = merged["quantity"].quantile(0.25)
Q3 = merged["quantity"].quantile(0.75)

IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

print("\nQ1:")
print(Q1)

print("\nQ3:")
print(Q3)

print("\nIQR:")
print(IQR)

print("\nLower bound:")
print(lower_bound)

print("\nUpper bound:")
print(upper_bound)


# ------------------------------------------------------------
# Flag outliers instead of deleting them
# ------------------------------------------------------------

merged["is_outlier"] = (
    (merged["quantity"] < lower_bound)
    | (merged["quantity"] > upper_bound)
)

outliers = merged.loc[
    merged["is_outlier"],
    ["order_id", "quantity"]
]

print("\nOutlier orders:")
print(outliers.to_string(index=False))

print("\nNumber of outliers detected:")
print(merged["is_outlier"].sum())

# ============================================================
# TASK 7 — HYPOTHESIS TEST: DOES COD HAVE A HIGHER RETURN RATE?
# ============================================================

print("\n" + "=" * 60)
print("TASK 7 — HYPOTHESIS: DOES COD HAVE A HIGHER RETURN RATE?")
print("=" * 60)

print(
    "\nHypothesis: COD orders have a higher return rate "
    "than CARD and UPI orders."
)

payment_return_summary = (
    merged
    .groupby("payment_method")["returned"]
    .agg(["count", "mean"])
)

payment_return_summary["return_rate_pct"] = (
    payment_return_summary["mean"] * 100
).round(1)

print("\nReturn rate by payment method:")
print(
    payment_return_summary[
        ["count", "return_rate_pct"]
    ]
)

cod_rate = payment_return_summary.loc["COD", "return_rate_pct"]
card_rate = payment_return_summary.loc["CARD", "return_rate_pct"]
upi_rate = payment_return_summary.loc["UPI", "return_rate_pct"]

print("\nSummary:")
print(f"CARD return rate: {card_rate:.1f}%")
print(f"COD return rate : {cod_rate:.1f}%")
print(f"UPI return rate : {upi_rate:.1f}%")

if cod_rate > card_rate and cod_rate > upi_rate:
    hypothesis_result = "Confirmed"
else:
    hypothesis_result = "Busted"

print(f"\nHypothesis result: {hypothesis_result}")

# ============================================================
# TASK 8 — MULTI-LEVEL SEGMENTATION
# ============================================================

print("\n" + "=" * 60)
print("TASK 8 — MULTI-LEVEL SEGMENTATION")
print("=" * 60)

segment_summary = (
    merged
    .groupby(["payment_method", "city_tier"])["returned"]
    .agg(["count", "mean"])
    .reset_index()
)

segment_summary["return_rate_pct"] = (
    segment_summary["mean"] * 100
).round(1)

print("\nReturn rate by payment method and city tier:")
print(
    segment_summary[
        ["payment_method", "city_tier", "count", "return_rate_pct"]
    ].to_string(index=False)
)


# ------------------------------------------------------------
# Identify highest-risk segment
# ------------------------------------------------------------

highest_risk_segment = segment_summary.loc[
    segment_summary["return_rate_pct"].idxmax()
]

print("\nHighest-risk segment:")
print(
    f"{highest_risk_segment['payment_method']} + "
    f"Tier-{int(highest_risk_segment['city_tier'])} cities"
)

print(
    f"Return rate: "
    f"{highest_risk_segment['return_rate_pct']:.1f}%"
)


# ------------------------------------------------------------
# Explicit COD comparison across city tiers
# ------------------------------------------------------------

cod_segments = segment_summary[
    segment_summary["payment_method"] == "COD"
]

print("\nCOD risk by city tier:")

for _, row in cod_segments.iterrows():
    print(
        f"COD + Tier-{int(row['city_tier'])}: "
        f"{int(row['count'])} orders, "
        f"{row['return_rate_pct']:.1f}% return rate"
    )

print(
    "\nConclusion: COD risk is not uniform across city tiers. "
    "Tier-2 COD orders have the highest return rate."
)

# ============================================================
# TASK 9 — CORRELATION ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("TASK 9 — CORRELATION ANALYSIS")
print("=" * 60)

correlation_columns = [
    "rating",
    "returned",
    "discount_pct",
    "quantity"
]

correlation_matrix = merged[
    correlation_columns
].corr()

print("\nCorrelation matrix:")
print(correlation_matrix.round(3))


# ------------------------------------------------------------
# Function to classify correlation strength
# ------------------------------------------------------------

def correlation_strength(value):
    absolute_value = abs(value)

    if absolute_value < 0.20:
        return "Negligible"
    elif absolute_value < 0.40:
        return "Weak"
    elif absolute_value < 0.70:
        return "Moderate"
    else:
        return "Strong"


# ------------------------------------------------------------
# Print all unique pairwise correlations
# ------------------------------------------------------------

print("\nPairwise correlation interpretation:")

for i in range(len(correlation_columns)):
    for j in range(i + 1, len(correlation_columns)):

        column_1 = correlation_columns[i]
        column_2 = correlation_columns[j]

        correlation_value = correlation_matrix.loc[
            column_1,
            column_2
        ]

        strength = correlation_strength(
            correlation_value
        )

        print(
            f"{column_1} vs {column_2}: "
            f"r = {correlation_value:.3f} "
            f"-> {strength}"
        )


# ------------------------------------------------------------
# Specific hypothesis:
# Higher discounts reduce returns
# ------------------------------------------------------------

discount_return_corr = correlation_matrix.loc[
    "discount_pct",
    "returned"
]

print("\nHypothesis:")
print("Higher discounts reduce returns.")

print(
    f"discount_pct vs returned correlation: "
    f"{discount_return_corr:.3f}"
)

if abs(discount_return_corr) < 0.20:
    discount_hypothesis_result = "Busted"
else:
    discount_hypothesis_result = "Supported"

print(
    f"Hypothesis result: "
    f"{discount_hypothesis_result}"
)

# ============================================================
# TASK 10 — OUTLIER-CORRECTED MONTHLY REVENUE TREND
# ============================================================

print("\n" + "=" * 60)
print("TASK 10 — OUTLIER-CORRECTED MONTHLY REVENUE TREND")
print("=" * 60)

# Convert order_date to datetime
merged["order_date"] = pd.to_datetime(merged["order_date"])

# Extract year-month
merged["year_month"] = merged["order_date"].dt.to_period("M")


# ------------------------------------------------------------
# Monthly revenue INCLUDING quantity outliers
# ------------------------------------------------------------

monthly_revenue_with_outliers = (
    merged
    .groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

print("\nMonthly revenue including outliers:")
print(monthly_revenue_with_outliers)


# ------------------------------------------------------------
# Monthly revenue EXCLUDING quantity outliers
# ------------------------------------------------------------

monthly_revenue_corrected = (
    merged.loc[~merged["is_outlier"]]
    .groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

print("\nOutlier-corrected monthly revenue:")
print(monthly_revenue_corrected)


# ------------------------------------------------------------
# Identify apparent and true peak months
# ------------------------------------------------------------

apparent_peak_month = monthly_revenue_with_outliers.idxmax()
apparent_peak_revenue = monthly_revenue_with_outliers.max()

true_peak_month = monthly_revenue_corrected.idxmax()
true_peak_revenue = monthly_revenue_corrected.max()


print("\nApparent peak month including outliers:")
print(
    f"{apparent_peak_month}: "
    f"₹{apparent_peak_revenue:,.2f}"
)

print("\nTrue peak month after excluding outliers:")
print(
    f"{true_peak_month}: "
    f"₹{true_peak_revenue:,.2f}"
)


# ------------------------------------------------------------
# Explain why January was misleading
# ------------------------------------------------------------

print("\nOutlier explanation:")

print(
    "January initially appears to be the highest-revenue month "
    "because the two bulk quantity orders O0011 and O0098 both "
    "occurred in January."
)

print(
    "O0011 occurred on 2026-01-28 with quantity 25, while "
    "O0098 occurred on 2026-01-10 with quantity 30."
)

print(
    "After excluding these two quantity outliers from the monthly "
    "trend analysis, March becomes the genuine peak month."
)

# ============================================================
# EXPORT VERIFIED FINDINGS FOR NARRATOR
# ============================================================

import json


print("\n" + "=" * 60)
print("EXPORTING VERIFIED FINDINGS")
print("=" * 60)

NARRATOR_DIR = BASE_DIR / "narrator"
NARRATOR_DIR.mkdir(exist_ok=True)

findings = {
    "cleaned_total_revenue_inr": round(float(cleaned_total_revenue), 2),
    "raw_total_revenue_inr": round(float(raw_total_revenue), 2),
    "duplicate_reconciliation_delta_inr": round(
        float(reconciliation_delta), 2
    ),

    "return_rate_by_payment": {
        "COD": float(cod_rate),
        "CARD": float(card_rate),
        "UPI": float(upi_rate)
    },

    "highest_risk_segment": {
        "payment_method": str(
            highest_risk_segment["payment_method"]
        ),
        "city_tier": int(
            highest_risk_segment["city_tier"]
        ),
        "return_rate_pct": float(
            highest_risk_segment["return_rate_pct"]
        )
    },

    "true_peak_month": {
        "month": str(true_peak_month),
        "revenue_inr": round(
            float(true_peak_revenue),
            2
        )
    },

    "outlier_inflated_month": {
        "month": str(apparent_peak_month),
        "apparent_revenue_inr": round(
            float(apparent_peak_revenue),
            2
        ),
        "corrected_revenue_inr": round(
            float(
                monthly_revenue_corrected.loc[
                    apparent_peak_month
                ]
            ),
            2
        )
    }
}

findings_path = NARRATOR_DIR / "findings.json"

with open(
    findings_path,
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        findings,
        file,
        indent=4
    )

print(f"\nFindings written to:")
print(findings_path)

print("\nExported findings:")
print(json.dumps(findings, indent=4))