-- models/staging/stg_prices.sql
-- -------------------------------------------------------------
-- STAGING model: the first clean layer on top of raw data.
-- Its job is simple: select from raw, rename/cast cleanly, and
-- give downstream models a tidy, trustworthy starting point.
--
-- dbt builds this as a VIEW (set in dbt_project.yml).
-- -------------------------------------------------------------

select
    ticker,
    date::date              as trade_date,
    open                    as open_price,
    high                    as high_price,
    low                     as low_price,
    close                   as close_price,
    volume
from {{ source('raw', 'raw_prices') }}
where close is not null
