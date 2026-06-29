"""
stock_pipeline_dag.py
===============================================================
DAY 3 of your project: SCHEDULE the pipeline with Airflow.

This DAG runs the exact same two steps you've been running by hand:
  1. extract_load  -> python extract_load.py
                       (yfinance -> pandas clean -> Postgres raw_prices)
  2. dbt_run        -> dbt run
                       (builds stg_prices + daily_metrics)

Airflow just runs them automatically, once a day, instead of you
typing the commands yourself. The DAG lives inside the Airflow
container, but it runs against the SAME project files — they're
mounted in at /opt/airflow/project (see docker-compose.yml).
===============================================================
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "stock_pipeline",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stock_pipeline_daily",
    description="Extract daily stock prices, load to Postgres, transform with dbt",
    default_args=default_args,
    schedule="@daily",          # runs once every day
    start_date=datetime(2026, 6, 1),
    catchup=False,               # don't backfill past missed runs
    tags=["stock", "etl"],
) as dag:

    # Step 1 — same as running `python extract_load.py` by hand.
    extract_load = BashOperator(
        task_id="extract_load",
        bash_command=f"cd {PROJECT_DIR} && python extract_load.py",
        append_env=True,   # keep PATH etc. so `python` is still found
    )

    # Step 2 — same as running `dbt run` by hand inside dbt_stock/.
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_DIR}/dbt_stock && dbt run",
        append_env=True,
    )

    extract_load >> dbt_run  # dbt_run only starts after extract_load succeeds
