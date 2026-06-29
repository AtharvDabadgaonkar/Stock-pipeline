-- models/marts/daily_metrics.sql
-- -------------------------------------------------------------
-- MARTS model: the FINAL, useful table investors care about.
-- This is the "T" (transform) payoff of your whole project.
--
-- It computes, per stock per day:
--   * daily_return_pct  -> % change vs the previous day
--   * moving_avg_7d      -> average close price over last 7 days
--   * daily_range        -> high minus low (intraday swing)
--
-- It uses WINDOW FUNCTIONS (LAG, AVG OVER) — a core SQL skill
-- worth understanding. Each is commented below.
--
-- dbt builds this as a TABLE (set in dbt_project.yml).
-- {{ ref('stg_prices') }} tells dbt to read from the staging model
-- and to build it FIRST — dbt figures out the order automatically.
-- -------------------------------------------------------------

with prices as (

    select * from {{ ref('stg_prices') }}

),

with_metrics as (

    select
        ticker,
        trade_date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,

        -- Intraday swing: how much the price moved within the day.
        high_price - low_price as daily_range,

        -- Previous day's close for THIS ticker.
        -- LAG looks "back" one row, partitioned per ticker so stocks
        -- don't bleed into each other, ordered by date.
        lag(close_price) over (
            partition by ticker
            order by trade_date
        ) as prev_close,

        -- 7-day moving average of the closing price.
        -- AVG over a window of the current row + 6 rows before it.
        avg(close_price) over (
            partition by ticker
            order by trade_date
            rows between 6 preceding and current row
        ) as moving_avg_7d

    from prices

)

select
    ticker,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    daily_range,
    prev_close,
    moving_avg_7d,

    -- Daily return as a percentage: (today - yesterday) / yesterday * 100.
    -- Guard against dividing by NULL on the first day of each stock.
    case
        when prev_close is not null and prev_close <> 0
        then round((((close_price - prev_close) / prev_close) * 100)::numeric, 2)
    end as daily_return_pct

from with_metrics
order by ticker, trade_date
