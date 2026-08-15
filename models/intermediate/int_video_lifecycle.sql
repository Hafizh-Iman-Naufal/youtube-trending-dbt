-- Intermediate: per-(region_code, video_id) lifecycle fields.
-- First/last trending date, observed trending days, time-from-publish
-- to first trending observation.

with obs as (
    select * from {{ ref('stg_youtube_video_observations') }}
)

select
    region_code,
    video_id,
    -- composite natural key (region + video) — see modeling-decisions D2
    {{ dbt_utils.generate_surrogate_key(['region_code', 'video_id']) }} as video_region_key,
    -- lifecycle dates
    min(trending_date_parsed)                          as first_trending_date,
    max(trending_date_parsed)                          as last_trending_date,
    -- distinct observed trending days (NOT the same as date_diff which
    -- would over-count gaps)
    count(distinct trending_date_parsed)               as observed_trending_days,
    -- first/last snapshot measures (point-in-time, not summed)
    max_by(views,        trending_date_parsed)         as latest_views,
    max_by(likes,        trending_date_parsed)         as latest_likes,
    max_by(dislikes,     trending_date_parsed)         as latest_dislikes,
    max_by(comment_count, trending_date_parsed)        as latest_comment_count,
    -- max observed (peak) — separate from latest
    max(views)                                          as peak_views,
    max(likes)                                          as peak_likes,
    max(dislikes)                                       as peak_dislikes,
    max(comment_count)                                  as peak_comment_count,
    -- publication context (taken from earliest observation since
    -- publish_time is stable per video in the source)
    min(publish_time)                                   as publish_time,
    -- days from publish to first trending appearance
    case
        when min(publish_time) is null then null
        else date_diff(
            'day',
            min(publish_time)::date,
            min(trending_date_parsed)
        )
    end as days_publish_to_first_trending
from obs
group by region_code, video_id
