-- Test to ensure no messages have future dates
SELECT
    message_id,
    message_date,
    channel_name
FROM {{ ref('fct_messages') }}
WHERE message_date > CURRENT_TIMESTAMP