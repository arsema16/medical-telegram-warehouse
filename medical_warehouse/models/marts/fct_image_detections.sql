{{
    config(
        materialized='table',
        schema='marts',
        tags=['marts', 'facts']
    )
}}

WITH detections AS (
    SELECT
        detection_id,
        message_id,
        channel_name,
        image_path,
        category,
        is_medical,
        total_detections,
        object_counts,
        top_objects,
        processed_at
    FROM fct_image_detections
),

messages AS (
    SELECT
        message_key,
        message_id,
        channel_key,
        date_key,
        views,
        forwards,
        replies,
        total_engagement
    FROM {{ ref('fct_messages') }}
)

SELECT
    d.detection_id,
    d.message_id,
    m.channel_key,
    m.date_key,
    m.views,
    m.forwards,
    m.replies,
    m.total_engagement,
    d.image_path,
    d.category AS image_category,
    d.is_medical,
    d.total_detections,
    d.object_counts,
    d.top_objects,
    -- Engagement by category
    CASE 
        WHEN d.category = 'promotional' THEN 'Promotional (Person + Product)'
        WHEN d.category = 'product_display' THEN 'Product Display'
        WHEN d.category = 'lifestyle' THEN 'Lifestyle (Person Only)'
        ELSE 'Other'
    END AS category_label,
    -- Medical object flag
    CASE 
        WHEN d.is_medical = 1 THEN 'Medical'
        ELSE 'Non-Medical'
    END AS medical_flag,
    d.processed_at
FROM detections d
LEFT JOIN messages m ON d.message_id = m.message_id