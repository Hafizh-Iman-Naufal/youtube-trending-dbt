-- Mart: per (region_code, category_id, trending_date) category performance.
-- Daily grain lets consumers see category-level trends over time.
select
    f.region_code,
    f.category_id,
    dc.category_title,
    f.trending_date,
    count(distinct f.video_id)            as distinct_videos,
    count(*)                              as observations,
    avg(case when f.has_valid_engagement then f.engagement_rate end) as avg_engagement_rate,
    avg(case when f.has_valid_engagement then f.like_rate end)        as avg_like_rate,
    avg(case when f.has_valid_engagement then f.dislike_rate end)     as avg_dislike_rate,
    avg(case when f.has_valid_engagement then f.comment_rate end)     as avg_comment_rate
from {{ ref('fct_video_trending_daily') }} f
left join {{ ref('dim_category') }} dc
    on f.region_code = dc.region_code and f.category_id = dc.category_id
group by f.region_code, f.category_id, dc.category_title, f.trending_date
