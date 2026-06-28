{{
    config(
        materialized='table',
        schema='marts',
        tags=['marts', 'dimensions']
    )
}}

WITH date_range AS (
    -- Generate date range from min to max dates in messages
    SELECT
        DATE_TRUNC('day', MIN(message_date)) AS min_date,
        DATE_TRUNC('day', MAX(message_date)) AS max_date
    FROM {{ ref('stg_telegram_messages') }}
),

dates AS (
    SELECT
        GENERATE_SERIES(
            (SELECT min_date FROM date_range),
            (SELECT max_date FROM date_range),
            INTERVAL '1 day'
        )::DATE AS date
),

dim_dates AS (
    SELECT
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['date']) }} AS date_key,
        date AS date_full,
        EXTRACT(EPOCH FROM date)::INTEGER AS date_epoch,
        EXTRACT(DOY FROM date) AS day_of_year,
        EXTRACT(DOW FROM date) AS day_of_week,
        TO_CHAR(date, 'Day') AS day_name,
        EXTRACT(WEEK FROM date) AS week_of_year,
        EXTRACT(MONTH FROM date) AS month_number,
        TO_CHAR(date, 'Month') AS month_name,
        EXTRACT(QUARTER FROM date) AS quarter,
        EXTRACT(YEAR FROM date) AS year,
        CASE
            WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend,
        -- First day of month
        DATE_TRUNC('month', date) AS first_day_of_month,
        -- Last day of month
        (DATE_TRUNC('month', date) + INTERVAL '1 month' - INTERVAL '1 day')::DATE AS last_day_of_month,
        -- Weekday flag
        CASE
            WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN 'Weekend'
            ELSE 'Weekday'
        END AS day_type
    FROM dates
)

SELECT * FROM dim_dates