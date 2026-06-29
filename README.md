# Stock Market Analytics Pipeline — ETL Project

A beginner-friendly **end-to-end data engineering project** built in 2 days.
It extracts daily stock prices, cleans them, loads them into a database,
and transforms them into investor-friendly metrics.

```
yfinance (Python)  ->  pandas clean  ->  PostgreSQL  ->  dbt transforms  ->  SQL answers
     EXTRACT              LIGHT T          LOAD            HEAVY T            ANALYSIS

                    (the whole thing above runs daily, automatically, via Airflow)
```

## What you'll learn
- The **ETL pattern** (Extract, Transform, Load) hands-on
- Running a database in **Docker** (no messy local installs)
- **Python + pandas** for extraction and cleaning
- **dbt + SQL** for real transformations (returns, moving averages, volatility)
- The pro pattern: light cleaning in Python, business logic in SQL

## Tools used
| Layer        | Tool                  |
|--------------|-----------------------|
| Extract      | Python, yfinance      |
| Storage      | PostgreSQL (Docker)   |
| Transform    | dbt                   |
| Analysis     | SQL                   |
| Orchestration| Apache Airflow (Docker) |

---

## ▶️ HOW TO RUN — follow in order

### Prerequisites
- Docker Desktop installed and running
- Python 3 installed (`python3 --version` to check)

---

### DAY 1 — Extract + Load

**1. Start the database (Docker):**
```bash
docker compose up -d
```
This downloads and runs PostgreSQL. Wait ~20 seconds the first time.

> If port `5432` is already used by a local Postgres install, this project
> maps the container to host port **5433** instead (see `docker-compose.yml`,
> `extract_load.py`, and `dbt_stock/profiles.yml` — all three agree on 5433).
> Change all three together if you'd rather use a different port.

**2. Set up Python and install libraries:**
```bash
python3 -m venv venv          # create an isolated Python environment
source venv/bin/activate      # turn it on (Mac/Linux)
pip install -r requirements.txt
```

**3. Run the ETL script:**
```bash
python extract_load.py
```
Success looks like: *"Done! Data is now in Postgres in the 'raw_prices' table."*

✅ **Day 1 complete** — raw, clean stock data is now in your database.

---

### DAY 2 — Transform with dbt + Analyze

**4. Install dbt (the Postgres version):**
```bash
pip install dbt-postgres
```

**5. Tell dbt how to connect** (copy the profile to where dbt expects it):
```bash
mkdir -p ~/.dbt
cp dbt_stock/profiles.yml ~/.dbt/profiles.yml
```

**6. Build your models:**
```bash
cd dbt_stock
dbt run
```
This creates `stg_prices` (clean view) and `daily_metrics` (final table
with returns, moving averages, etc.) inside Postgres.

**7. (Optional but nice) Run dbt's built-in tests & docs:**
```bash
dbt docs generate
dbt docs serve     # opens a browser diagram of your pipeline
```

**8. Answer real questions:**
Run the queries in `analysis_queries.sql` against Postgres:
```bash
docker exec -i stock_postgres psql -U stock_user -d stock_db < analysis_queries.sql
```
They answer:
- Which stock was most volatile?
- Biggest single-day gains and drops?
- Average trading volume?
- Latest momentum (7-day moving average)?

✅ **Day 2 complete — full ETL pipeline done!**

---

### DAY 3 — Schedule it with Airflow

Steps 1–8 above are still useful to run by hand, but the real goal of a
pipeline is to run itself. The `airflow` service in `docker-compose.yml`
runs Apache Airflow in standalone mode (webserver + scheduler in one
container) and points it at this same project folder.

**9. Start Airflow** (Postgres should already be up from step 1):
```bash
docker compose up -d
```
First boot installs the pipeline's Python packages into the Airflow
container (yfinance, pandas, dbt-postgres, etc.) — give it a couple of
minutes. Watch progress with `docker logs -f stock_airflow`.

**10. Log in to the Airflow UI:** open **http://localhost:8081**.
The container creates an `admin` user with the username/password set
in `docker-compose.yml` (`_AIRFLOW_WWW_USER_USERNAME` / `_PASSWORD`).
If standalone mode generated its own random password instead, grab it with:
```bash
docker exec stock_airflow cat /opt/airflow/standalone_admin_password.txt
```
or just reset it directly:
```bash
docker exec -it stock_airflow airflow users delete --username admin
docker exec -it stock_airflow airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
```

**11. Turn on the DAG:** find `stock_pipeline_daily` in the DAGs list,
flip its toggle on (DAGs start paused), then hit the ▶ "Trigger DAG"
button to run it once immediately. It runs two tasks in order —
`extract_load` then `dbt_run` — the exact same commands from Days 1–2,
just automated. It's scheduled to repeat once every day after that.

✅ **Day 3 complete — the pipeline now runs itself.**


- **Airflow `extract_load` task stuck in `up_for_retry`** → check its logs in the UI. A common cause: `to_sql(if_exists="replace")` tries to `DROP TABLE raw_prices`, which fails once dbt has built views on top of it — this project truncates instead of dropping, to avoid that.
- Stuck on anything → paste the error into Claude Code and let it fix it.
