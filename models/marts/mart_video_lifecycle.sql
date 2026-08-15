-- Mart: per (region_code, video_id) video lifecycle summary.
-- Source: int_video_lifecycle (no fact joins needed; lifecycle is
-- already aggregated per video-region).
select
    video_region_key,
    region_code,
    video_id,
    first_trending_date,
    last_trending_date,
    observed_trending_days,
    latest_views,
    peak_views,
    latest_likes,
    peak_likes,
    latest_dislikes,
    peak_dislikes,
    latest_comment_count,
    peak_comment_count,
    publish_time,
    days_publish_to_first_trending
from {{ ref('int_video_lifecycle') }}
