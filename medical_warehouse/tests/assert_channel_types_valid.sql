-- Test to ensure channel types are valid
SELECT
    channel_key,
    channel_name,
    channel_type
FROM {{ ref('dim_channels') }}
WHERE channel_type NOT IN ('Medical', 'Cosmetics', 'Pharmaceutical', 'Other')