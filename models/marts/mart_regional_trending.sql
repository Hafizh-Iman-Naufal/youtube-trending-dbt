-- Mart: per (region_code, trending_date) regional trending overview.
select
    region_code,
    trending_date,
    count(distinct video_id)               as distinct_videos,
    count(*)                               as observations,
    count(distinct category_id)            as active_categories,
    count(distinct channel_title)          as active_channels,
    avg(case when has_valid_engagement then engagement_rate end) as avg_engagement_rate,
    avg(case when has_valid_engagement then like_rate end)        as avg_like_rate
from {{ ref('fct_video_trending_daily') }}
group by region_code, trending_date
