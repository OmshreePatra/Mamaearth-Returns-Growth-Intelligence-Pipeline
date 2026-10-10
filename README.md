# Mamaearth Returns & Growth Intelligence Pipeline

An end-to-end analytics pipeline for Mamaearth order and return data using SQL, Python/pandas, Matplotlib, and a GenAI insight narrator with a deterministic offline fallback.


## Project Objective

The goal of this project is to identify how returns affect revenue, clean and validate the raw order data, detect high-risk return segments, correct misleading revenue trends caused by outliers, and convert the verified findings into a business-friendly Situation–Complication–Resolution narrative.

## Pipeline

~~~text
Raw CSV Data
    ↓
SQLite Relational Layer
    ↓
SQL Reports
    ↓
Python/pandas Cleaning and EDA
    ↓
Visualizations
    ↓
findings.json
    ↓
Gemini / Offline SCR Narrator
~~~

Every reported number is generated from the data and passed forward through the pipeline.

---

## Repository Structure

~~~text
mamaearth_returns_growth_intelligence_pipeline/
│
├── README.md
│
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
│
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
│
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
│
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
│
└── narrator/
    ├── findings.json
    ├── generate_narrative.py
    └── sample_output.txt
~~~

---

## Current Project Status

- [x] Raw datasets preserved exactly as supplied
- [x] SQL relational schema
- [x] Re-runnable SQL seed script
- [x] SQL reporting queries
- [x] pandas cleaning and EDA
- [x] Payment-method standardization
- [x] Duplicate-order detection and removal
- [x] Missing-value imputation
- [x] Revenue reconciliation
- [x] IQR outlier detection
- [x] Return-rate hypothesis analysis
- [x] Multi-level segmentation
- [x] Correlation analysis
- [x] Outlier-corrected monthly revenue analysis
- [x] Matplotlib visualizations
- [x] Automatic `findings.json` export
- [x] Deterministic offline SCR narrator
- [x] Numeric accuracy checker
- [x] Offline fallback testing
- [ ] Successful live Gemini sample

The Gemini integration is implemented, but the current Google API project is returning a permission-denied response. The deterministic offline fallback remains fully functional and allows the project to run without network access or an API key.

---

## Part 1 — SQL Relational Layer

The SQL layer creates and loads three relational tables:

- `customers`
- `products`
- `orders`

The `orders` table references `customers` and `products` using foreign keys.

### Run the SQL Layer

From the project root, start SQLite:

~~~powershell
sqlite3 mamaearth.db
~~~

Inside the SQLite prompt:

~~~sql
PRAGMA foreign_keys = ON;

.read sql/schema.sql
.read sql/seed_data.sql
.read sql/reports.sql
~~~

After completion, exit SQLite:

~~~sql
.quit
~~~

### Expected Row Counts

~~~text
customers = 45
products  = 16
orders    = 180
~~~

### Key SQL Results

~~~text
Total orders        = 180
Total revenue       = ₹99,860.20
Average order value = ₹554.78

Missing ratings     = 15
~~~

Customer with no orders:

~~~text
C045 | Vihaan
~~~

Cities with return rate above 20%:

~~~text
Jaipur    | 19 orders | 8 returns  | 42.1%
Lucknow   | 49 orders | 15 returns | 30.6%
Bangalore | 33 orders | 8 returns  | 24.2%
~~~

Top customer by total spend:

~~~text
C043 | Reyansh | ₹12,920.00
~~~

Category revenue:

~~~text
Haircare     | 54 orders | ₹44,956.10
Skincare     | 60 orders | ₹27,346.00
Babycare     | 30 orders | ₹16,805.00
PersonalCare | 36 orders | ₹10,753.10
~~~

Loyalty-tier result:

~~~text
Gold   | 28
Silver | 17
~~~

---

## Part 2 — Python/Pandas Cleaning and EDA

The Python analysis reads the original CSV files directly from `data/`.

The raw CSV files are never manually edited.

Run:

~~~powershell
py analysis\clean_and_eda.py
~~~

The script performs the following steps:

1. Loads and inspects all three CSV files.
2. Standardizes `payment_method`.
3. Detects and removes duplicate business transactions.
4. Imputes missing discounts and ratings.
5. Merges orders with products and customers.
6. Calculates `order_value`.
7. Reconciles cleaned revenue with raw SQL revenue.
8. Detects quantity outliers using the IQR method.
9. Tests whether COD has a higher return rate.
10. Performs payment-method and city-tier segmentation.
11. Computes the correlation matrix.
12. Compares monthly revenue with and without quantity outliers.
13. Writes the verified findings to `narrator/findings.json`.

---

## Data Cleaning Results

### Payment-Method Standardization

Raw payment-method values:

~~~text
COD
cod
Card
card
CARD
UPI
upi
~~~

After standardization:

~~~text
CARD
COD
UPI
~~~

Raw counts:

~~~text
CARD = 70
UPI  = 55
COD  = 55
~~~

---

## Duplicate Removal

Five duplicate business transactions are detected:

~~~text
O0176
O0177
O0178
O0179
O0180
~~~

Orders before cleaning:

~~~text
180
~~~

Orders after duplicate removal:

~~~text
175
~~~

---

## Missing-Value Handling

Missing `discount_pct` values:

~~~text
12
~~~

These are filled with `0`, representing no promotional discount.

Missing `rating` values:

~~~text
15
~~~

The median rating before imputation is:

~~~text
3.0
~~~

After imputation:

~~~text
discount_pct missing = 0
rating missing       = 0
~~~

---

## Revenue Reconciliation

Raw SQL revenue:

~~~text
₹99,860.20
~~~

Cleaned revenue:

~~~text
₹97,358.30
~~~

Difference:

~~~text
₹2,501.90
~~~

The complete ₹2,501.90 difference is caused by the five duplicate transactions removed during cleaning.

Discount and rating imputation do not change the revenue total.

---

## IQR Outlier Detection

The IQR method is applied to the `quantity` column.

~~~text
Q1          = 1.0
Q3          = 2.0
IQR         = 1.0
Lower bound = -0.5
Upper bound = 3.5
~~~

Two quantity outliers are identified:

~~~text
O0011 | quantity = 25
O0098 | quantity = 30
~~~

The outliers are flagged rather than deleted from the cleaned dataset.

---

## Return-Rate Hypothesis

Hypothesis:

> COD orders have a higher return rate than CARD and UPI orders.

Results:

~~~text
CARD = 14.7%
COD  = 44.4%
UPI  = 18.9%
~~~

Conclusion:

~~~text
Confirmed
~~~

---

## Multi-Level Segmentation

Return rates are further segmented by payment method and city tier.

The highest-risk segment is:

~~~text
COD + Tier-2 cities = 54.5%
~~~

COD comparison:

~~~text
COD + Tier-1 = 32 orders | 37.5%
COD + Tier-2 = 22 orders | 54.5%
~~~

This demonstrates that COD return risk is not distributed uniformly across city tiers.

---

## Correlation Analysis

Correlation is calculated across:

- `rating`
- `returned`
- `discount_pct`
- `quantity`

All six unique pairwise relationships fall into the negligible correlation band.

Example:

~~~text
discount_pct vs returned = -0.088
~~~

Therefore the hypothesis:

> Higher discounts reduce returns.

is classified as:

~~~text
Busted
~~~

---

## Outlier-Corrected Monthly Revenue

Monthly revenue including quantity outliers:

~~~text
2026-01 = ₹29,582.10
2026-02 = ₹13,195.50
2026-03 = ₹20,318.90
2026-04 = ₹9,495.30
2026-05 = ₹13,151.10
2026-06 = ₹11,615.40
~~~

Outlier-corrected monthly revenue:

~~~text
2026-01 = ₹11,637.10
2026-02 = ₹13,195.50
2026-03 = ₹20,318.90
2026-04 = ₹9,495.30
2026-05 = ₹13,151.10
2026-06 = ₹11,615.40
~~~

January initially appears to be the highest-revenue month because both bulk-order outliers occur in January:

~~~text
O0011 | 2026-01-28 | quantity 25
O0098 | 2026-01-10 | quantity 30
~~~

After excluding these two outliers from trend analysis:

~~~text
True peak month = March 2026
Revenue         = ₹20,318.90
~~~

---

## Visualizations

Run:

~~~powershell
py analysis\visualize.py
~~~

The script generates:

~~~text
visualizations/return_rate_by_payment.png
visualizations/monthly_revenue_trend.png
~~~

`return_rate_by_payment.png` shows the cleaned return rate by payment method.

`monthly_revenue_trend.png` shows the outlier-corrected monthly revenue trend and identifies March 2026 as the true peak month.

---

## Part 3 — GenAI Insight Narrator

The Python analysis automatically writes verified results to:

~~~text
narrator/findings.json
~~~

The file contains values generated directly from the analysis pipeline.

Important values include:

~~~text
Cleaned revenue                = ₹97,358.30
Raw revenue                    = ₹99,860.20
Duplicate reconciliation delta = ₹2,501.90

COD return rate  = 44.4%
CARD return rate = 14.7%
UPI return rate  = 18.9%

Highest-risk segment:
COD + Tier-2 = 54.5%

True peak:
March 2026 = ₹20,318.90
~~~

---

## Offline SCR Narrator

Run:

~~~powershell
py narrator\generate_narrative.py
~~~

If `GEMINI_API_KEY` is not configured, the script automatically uses the deterministic offline narrator.

The output follows the required SCR structure:

~~~text
Situation
Complication
Resolution
~~~

The offline narrator requires:

- no network connection
- no API key
- no paid service

This makes the complete pipeline reproducible even when Gemini is unavailable.

---

## Gemini API Mode

To use the Gemini path, configure the API key as an environment variable.

In PowerShell:

~~~powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
~~~

Then run:

~~~powershell
py narrator\generate_narrative.py
~~~

The Gemini configuration includes:

~~~text
temperature       = 0.0
max_output_tokens = 500
timeout           = 15 seconds
~~~

The factual system instruction requires:

- exactly three SCR sections
- all numbers to originate from `findings.json`
- no invented statistics

If Gemini is unavailable or the request fails, the project automatically uses the deterministic offline fallback.

To remove the temporary environment variable:

~~~powershell
Remove-Item Env:GEMINI_API_KEY
~~~

Never commit an API key to GitHub.

---

## Numeric Accuracy Checker

The narrator includes a numeric accuracy checker.

The generated narrative must contain the following verified figures:

~~~text
₹97,358.30
44.4%
54.5%
₹2,501.90
March
₹20,318.90
~~~

The checker prints a PASS or FAIL result for every required value.

A successful offline run produces:

~~~text
cleaned_total_revenue: PASS
cod_return_rate: PASS
highest_risk_segment: PASS
duplicate_delta: PASS
true_peak_month: PASS
true_peak_revenue: PASS

Overall checker result:
PASS
~~~

---

## Full Reproduction Sequence

A new user can reproduce the complete project in the following order.

### 1. SQL Layer

~~~powershell
sqlite3 mamaearth.db
~~~

Inside SQLite:

~~~sql
PRAGMA foreign_keys = ON;

.read sql/schema.sql
.read sql/seed_data.sql
.read sql/reports.sql

.quit
~~~

### 2. Python Cleaning and EDA

~~~powershell
py analysis\clean_and_eda.py
~~~

This regenerates:

~~~text
narrator/findings.json
~~~

### 3. Visualizations

~~~powershell
py analysis\visualize.py
~~~

This regenerates:

~~~text
visualizations/return_rate_by_payment.png
visualizations/monthly_revenue_trend.png
~~~

### 4. Insight Narrator

Without an API key:

~~~powershell
py narrator\generate_narrative.py
~~~

With Gemini:

~~~powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
py narrator\generate_narrative.py
~~~

---

## Key Business Findings

- Verified cleaned revenue is **₹97,358.30**.
- Five duplicate orders inflated raw revenue by **₹2,501.90**.
- COD has the highest return rate at **44.4%**.
- COD orders from Tier-2 cities are the highest-risk segment at **54.5%**.
- Discounts show negligible correlation with returns.
- January's apparent revenue lead is caused by two unusually large quantity orders.
- March 2026 is the genuine peak month with **₹20,318.90** in outlier-corrected revenue.

---

## Technology Stack

- SQLite
- SQL
- Python
- pandas
- Matplotlib
- JSON
- Google GenAI SDK
- Git
- GitHub
- VS Code

---

## Final Conclusion

The project demonstrates how raw transactional data can produce misleading business conclusions when duplicates, missing values, segmentation, and outliers are ignored.

The strongest operational finding is the high return rate among COD orders, particularly in Tier-2 cities.

The complete pipeline therefore provides a reproducible workflow from relational data storage through cleaning and exploratory analysis to visualization and business-facing SCR narration.