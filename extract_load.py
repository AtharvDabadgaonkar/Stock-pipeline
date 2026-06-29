"""
extract_load.py
===============================================================
DAY 1 of your project: EXTRACT and LOAD.

What this script does, step by step:
  1. EXTRACT  -> download daily stock prices using yfinance
  2. TRANSFORM (light) -> clean the data in pandas (nulls, dates, dupes)
  3. LOAD     -> save it into your Postgres database

The heavier business transformations (returns, moving averages)
happen LATER in dbt on Day 2 — that separation is exactly how real
data engineering works: light cleaning in Python, business logic in SQL.

Run it with:   python extract_load.py
===============================================================
"""

import os

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, inspect, text

# ---------------------------------------------------------------
# CONFIG — change these if you want different stocks or date range
# ---------------------------------------------------------------
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]  # 5 well-known stocks
START_DATE = "2023-01-01"   # how far back to pull data
END_DATE = "2024-01-01"     # up to (not including) this date

# Connection string to YOUR Postgres running in Docker.
# Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE
# DB_HOST/DB_PORT can be overridden by env vars:
#   - running by hand on your Mac    -> defaults (localhost:5433)
#   - running inside the Airflow container -> set to postgres:5432
#     (the Docker network's internal hostname/port for the same DB)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_URL = f"postgresql://stock_user:stock_pass@{DB_HOST}:{DB_PORT}/stock_db"


def extract(tickers, start, end):
    """STEP 1 — EXTRACT: download raw price data from Yahoo Finance."""
    print(f"Downloading data for: {tickers}")

    # yfinance returns a table with Date as the index and columns
    # like Open, High, Low, Close, Volume for each ticker.
    raw = yf.download(tickers, start=start, end=end, group_by="ticker")

    # Reshape the messy multi-level table into a simple long format:
    # one row per (ticker, date). This is much easier to load & query.
    frames = []
    for ticker in tickers:
        df = raw[ticker].copy()          # grab this ticker's sub-table
        df["ticker"] = ticker            # remember which stock it is
        df = df.reset_index()            # turn the Date index into a column
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    print(f"Downloaded {len(combined)} rows total.")
    return combined


def transform_light(df):
    """STEP 2 — LIGHT TRANSFORM: basic cleaning only."""
    print("Cleaning data...")

    # Make column names lowercase and snake_case (easier in SQL).
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]

    # Keep only the columns we care about.
    keep = ["date", "ticker", "open", "high", "low", "close", "volume"]
    df = df[keep]

    # Drop rows where the closing price is missing — they're useless.
    df = df.dropna(subset=["close"])

    # Make sure the date column is a real date type.
    df["date"] = pd.to_datetime(df["date"])

    # Remove any exact duplicate rows just in case.
    df = df.drop_duplicates()

    print(f"After cleaning: {len(df)} rows.")
    return df


def load(df, db_url):
    """STEP 3 — LOAD: write the clean data into Postgres."""
    print("Connecting to Postgres and loading data...")

    engine = create_engine(db_url)

    # Write to a table called 'raw_prices'.
    # We TRUNCATE + re-insert instead of using if_exists='replace'.
    # 'replace' issues a DROP TABLE, which fails once dbt has built
    # stg_prices/daily_metrics on top of raw_prices (Postgres won't
    # drop a table that other views/tables depend on). Truncating
    # clears the rows but keeps the table object — and the dbt
    # objects built on top of it — intact, so this is safe to run
    # again and again (by hand, or daily via Airflow).
    with engine.begin() as conn:
        if inspect(engine).has_table("raw_prices"):
            conn.execute(text("TRUNCATE TABLE raw_prices"))

    df.to_sql("raw_prices", engine, if_exists="append", index=False)

    print("Done! Data is now in Postgres in the 'raw_prices' table.")


def main():
    """Run the full Extract -> Transform -> Load pipeline."""
    data = extract(TICKERS, START_DATE, END_DATE)
    clean = transform_light(data)
    load(clean, DB_URL)
    print("\nETL complete. You can now move on to Day 2 (dbt).")


if __name__ == "__main__":
    main()
