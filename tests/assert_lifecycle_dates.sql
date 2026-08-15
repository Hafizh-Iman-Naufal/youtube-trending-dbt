-- Returns rows where first_trending_date > last_trending_date, or
-- observed_trending_days is invalid.
select
    region_code,
    video_id,
    first_trending_date,
    last_trending_date,
    observed_trending_days
from {{ ref('int_video_lifecycle') }}
where
    first_trending_date > last_trending_date
    or observed_trending_days < 1
