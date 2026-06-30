{{
    config(
        materialized='table',
        schema='marts',
        tags=['marts', 'facts']
    )
}}

WITH messages AS (
    SELECT
        message_id,
        channel_name,
        message_date,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        replies,
        message_length,
        channel_type
    FROM {{ ref('stg_telegram_messages') }}
),

channels AS (
    SELECT
        channel_key,
        channel_name
    FROM {{ ref('dim_channels') }}
),

dates AS (
    SELECT
        date_key,
        date_full
    FROM {{ ref('dim_dates') }}
)

SELECT
    -- Surrogate key for fact table
    {{ dbt_utils.generate_surrogate_key(['m.message_id', 'm.message_date']) }} AS message_key,
    m.message_id,
    c.channel_key,
    d.date_key,
    m.message_text,
    m.message_length,
    m.views,
    m.forwards,
    m.replies,
    m.has_media,
    m.image_path,
    -- Calculated metrics
    CASE
        WHEN m.message_length > 0 THEN TRUE
        ELSE FALSE
    END AS has_text,
    -- Engagement metrics
    COALESCE(m.views, 0) + COALESCE(m.forwards, 0) + COALESCE(m.replies, 0) AS total_engagement,
    -- Content categorization
    CASE
        WHEN m.message_text ILIKE '%price%' OR m.message_text ILIKE '%birr%' OR m.message_text ILIKE '%ETB%' THEN 'Pricing'
        WHEN m.message_text ILIKE '%available%' OR m.message_text ILIKE '%stock%' THEN 'Availability'
        WHEN m.message_text ILIKE '%new%' OR m.message_text ILIKE '%arrival%' THEN 'New Product'
        WHEN m.message_text ILIKE '%discount%' OR m.message_text ILIKE '%sale%' OR m.message_text ILIKE '%promo%' THEN 'Promotion'
        ELSE 'General'
    END AS content_category,
    CURRENT_TIMESTAMP AS updated_at
FROM messages m
LEFT JOIN channels c ON m.channel_name = c.channel_name
LEFT JOIN dates d ON DATE_TRUNC('day', m.message_date) = d.date_full
WHERE m.message_date IS NOT NULL