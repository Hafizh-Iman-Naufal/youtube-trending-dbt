-- Mart: per (region_code, channel_title) channel performance.
-- channel_title is a display label (NOT a stable FK); grouping by it
-- surfaces label collisions as duplicates in the result. Document in
-- the model description.
with lifecycle as (
    select * from {{ ref('int_video_lifecycle') }}
),

obs as (
    select region_code, video_id, channel_title, has_valid_engagement,
           engagement_rate
    from {{ ref('fct_video_trending_daily') }}
),

per_video as (
    -- one row per (region, video) carrying the channel label + measures
    select
        o.region_code,
        o.video_id,
        any_value(o.channel_title) as channel_title,
        max(l.latest_views)        as latest_views,
        max(l.peak_views)          as peak_views,
        max(l.observed_trending_days) as observed_trending_days,
        max(case when o.has_valid_engagement then o.engagement_rate end) as latest_engagement_rate
    from obs o
    join lifecycle l
        on o.region_code = l.region_code and o.video_id = l.video_id
    group by o.region_code, o.video_id
)

select
    region_code,
    channel_title,
    count(distinct video_id)              as distinct_videos,
    sum(observed_trending_days)           as total_trending_days,
    avg(latest_views)                     as avg_latest_views,
    avg(peak_views)                       as avg_peak_views,
    avg(latest_engagement_rate)           as avg_engagement_rate
from per_video
group by region_code, channel_title
