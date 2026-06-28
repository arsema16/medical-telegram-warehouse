-- Test to ensure view counts are non-negative
SELECT
    message_id,
    views,
    channel_name
FROM {{ ref('fct_messages') }}
WHERE views < 0