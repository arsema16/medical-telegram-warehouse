{{
    config(
        materialized='view',
        schema='staging',
        tags=['staging']
    )
}}

WITH source AS (
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
        scraped_at,
        raw_data
    FROM raw.telegram_messages
),

cleaned AS (
    SELECT
        message_id,
        TRIM(channel_name) AS channel_name,
        message_date,
        COALESCE(message_text, '') AS message_text,
        COALESCE(has_media, FALSE) AS has_media,
        image_path,
        COALESCE(views, 0) AS views,
        COALESCE(forwards, 0) AS forwards,
        COALESCE(replies, 0) AS replies,
        scraped_at,
        -- Calculate message length
        LENGTH(COALESCE(message_text, '')) AS message_length,
        -- Extract channel type from name (simplified classification)
        CASE
            WHEN LOWER(channel_name) LIKE '%chemed%' OR LOWER(channel_name) LIKE '%medical%' THEN 'Medical'
            WHEN LOWER(channel_name) LIKE '%lobelia%' OR LOWER(channel_name) LIKE '%cosmetic%' THEN 'Cosmetics'
            WHEN LOWER(channel_name) LIKE '%tikvah%' OR LOWER(channel_name) LIKE '%pharma%' THEN 'Pharmaceutical'
            ELSE 'Other'
        END AS channel_type
    FROM source
    -- Filter out invalid messages
    WHERE message_id IS NOT NULL
        AND channel_name IS NOT NULL
        AND channel_name != ''
)

SELECT * FROM cleaned