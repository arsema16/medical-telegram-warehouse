{{
    config(
        materialized='table',
        schema='marts',
        tags=['marts', 'dimensions']
    )
}}

WITH channel_stats AS (
    SELECT
        channel_name,
        MIN(message_date) AS first_post_date,
        MAX(message_date) AS last_post_date,
        COUNT(*) AS total_posts,
        AVG(views) AS avg_views,
        MAX(channel_type) AS channel_type  -- Use first/any channel_type
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name
)

SELECT
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['channel_name']) }} AS channel_key,
    channel_name,
    channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    ROUND(avg_views, 2) AS avg_views,
    -- Calculate days active
    DATE_PART('day', last_post_date - first_post_date) + 1 AS days_active,
    -- Calculate posts per day
    CASE
        WHEN DATE_PART('day', last_post_date - first_post_date) + 1 > 0
        THEN ROUND(CAST(total_posts AS DECIMAL) / (DATE_PART('day', last_post_date - first_post_date) + 1), 2)
        ELSE total_posts
    END AS posts_per_day,
    CURRENT_TIMESTAMP AS updated_at
FROM channel_stats