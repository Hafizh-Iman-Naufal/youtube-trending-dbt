-- Core dimension: one row per (region_code, video_id).
-- Source: staged observations, picking the LATEST observation's metadata
-- for representative current attributes (title, channel, publish_time,
-- thumbnail, description). Metadata can change across daily observations;
-- this is a current/representative dimension, not a Type-2 history.

with obs as (
    select * from {{ ref('stg_youtube_video_observations') }}
),

ranked as (
    select
        region_code,
        video_id,
        title,
        channel_title,
        category_id,
        publish_time,
        thumbnail_link,
        description,
        comments_disabled,
        ratings_disabled,
        video_error_or_removed,
        row_number() over (
            partition by region_code, video_id
            order by trending_date_parsed desc, _loaded_at desc
        ) as rn
    from obs
)

select
    {{ dbt_utils.generate_surrogate_key(['region_code', 'video_id']) }} as video_key,
    region_code,
    video_id,
    title,
    channel_title,
    category_id,
    publish_time,
    thumbnail_link,
    description,
    comments_disabled,
    ratings_disabled,
    video_error_or_removed
from ranked
where rn = 1
