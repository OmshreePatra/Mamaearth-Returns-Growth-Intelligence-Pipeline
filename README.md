# Mamaearth Returns & Growth Intelligence Pipeline

An end-to-end analytics pipeline for Mamaearth order and return data using SQL, Python/pandas, Matplotlib, and a GenAI insight narrator with a deterministic offline fallback.


## Project Objective

The goal of this project is to identify how returns affect revenue, clean and validate the raw order data, detect high-risk return segments, correct misleading revenue trends caused by outliers, and convert the verified findings into a business-friendly Situation–Complication–Resolution narrative.

## Pipeline

1. Raw CSV Data
2. SQLite Relational Layer
3. SQL Reports
4. Python/pandas Cleaning and EDA
5. Visualizations
6. `findings.json`
7. Gemini / Offline SCR Narrator

Every reported number is generated from the data and passed forward through the pipeline.

---

## Repository Structure

- `README.md`
- `data/`
  - `customers.csv`
  - `products.csv`
  - `orders.csv`
- `sql/`
  - `schema.sql`
  - `seed_data.sql`
  - `reports.sql`
- `analysis/`
  - `clean_and_eda.py`
  - `visualize.py`
- `visualizations/`
  - `return_rate_by_payment.png`
  - `monthly_revenue_trend.png`
- `narrator/`
  - `findings.json`
  - `generate_narrative.py`
  - `sample_output.txt`