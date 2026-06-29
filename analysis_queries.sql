-- analysis_queries.sql
-- =============================================================
-- DAY 2 afternoon: answer real questions using your final table.
-- Run these in Postgres (Claude Code can run them, or use any
-- SQL tool / the psql command line). Each answers a question an
-- investor would actually ask.
-- =============================================================


-- Q1. Which stock was the MOST VOLATILE?
-- We use the standard deviation of daily returns as the volatility
-- measure. Higher = more bouncy/risky.
select
    ticker,
    round(stddev(daily_return_pct)::numeric, 2) as volatility
from daily_metrics
group by ticker
order by volatility desc;


-- Q2. Which stock had the BEST single-day gain, and when?
select
    ticker,
    trade_date,
    daily_return_pct
from daily_metrics
order by daily_return_pct desc nulls last
limit 5;


-- Q3. Which stock had the WORST single-day drop?
select
    ticker,
    trade_date,
    daily_return_pct
from daily_metrics
order by daily_return_pct asc nulls last
limit 5;


-- Q4. Average daily trading volume per stock (a liquidity proxy).
select
    ticker,
    round(avg(volume)) as avg_daily_volume
from daily_metrics
group by ticker
order by avg_daily_volume desc;


-- Q5. Most recent 7-day moving average per stock — a simple
-- momentum snapshot of where each stock is trending.
select distinct on (ticker)
    ticker,
    trade_date,
    round(close_price::numeric, 2) as close_price,
    round(moving_avg_7d::numeric, 2) as moving_avg_7d
from daily_metrics
order by ticker, trade_date desc;
