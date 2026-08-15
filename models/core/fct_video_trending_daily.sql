-- Core fact: one row per (region_code, video_id, trending_date) trending observation.
-- Grain: the same as stg_youtube_video_observations.
-- Includes snapshot measures + derived rates via intermediate enrichment.

select
    e.observation_key,
    e.region_code,
    e.video_id,
    e.trending_date_parsed                                       as trending_date,
    -- FKs (region_code + category_id are natural keys; video_key is surrogate)
    r.region_key,
    v.video_key,
    c.category_key,
    -- content attributes carried for convenience
    e.title,
    e.channel_title,
    e.category_id,
    e.publish_time,
    e.days_since_publish,
    -- snapshot measures
    e.views,
    e.likes,
    e.dislikes,
    e.comment_count,
    -- derived rates (NULL where has_valid_engagement=false)
    e.like_rate,
    e.dislike_rate,
    e.comment_rate,
    e.engagement_rate,
    e.has_valid_engagement,
    -- data-quality flags
    e.comments_disabled,
    e.ratings_disabled,
    e.video_error_or_removed,
    -- tags
    e.tags_raw,
    e.tags_normalized,
    e.tag_count
from {{ ref('int_video_observations_enriched') }} e
left join {{ ref('dim_region') }}  r on e.region_code = r.region_code
left join {{ ref('dim_video') }}    v
    on e.region_code = v.region_code and e.video_id = v.video_id
left join {{ ref('dim_category') }} c
    on e.region_code = c.region_code and e.category_id = c.category_id
