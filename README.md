# Mamaearth Returns & Growth Intelligence Pipeline

An end-to-end analytics pipeline for Mamaearth order and return data using SQL, Python/pandas, Matplotlib, and a GenAI insight narrator with a deterministic offline fallback.

## Project Objective

The goal of this project is to identify how returns affect revenue, clean and validate the raw order data, detect high-risk return segments, correct misleading revenue trends caused by outliers, and convert the verified findings into a business-friendly Situation–Complication–Resolution narrative.


## Pipeline

```text
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

Every reported number is generated from the data and passed forward through the pipeline.

---

## Repository Structure

```text
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