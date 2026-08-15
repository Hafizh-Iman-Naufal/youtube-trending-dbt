-- Intermediate: enriched observations joined to category metadata
-- + point-in-time engagement rates (snapshot semantics).
-- Does NOT compute lifecycle — that lives in int_video_lifecycle.

with obs as (
    select * from {{ ref('stg_youtube_video_observations') }}
),

cat as (
    select * from {{ ref('stg_youtube_categories') }}
),

joined as (
    select
        obs.*,
        cat.category_title,
        cat.assignable as category_assignable
    from obs
    left join cat
        on obs.region_code = cat.region_code
       and obs.category_id = cat.category_id
)

select
    -- identifiers
    region_code,
    video_id,
    trending_date,
    trending_date_parsed,
    observation_key,
    -- content
    title,
    channel_title,
    category_id,
    category_title,
    category_assignable,
    -- timestamps
    publish_time,
    case
        when publish_time is null then null
        else date_diff('day', publish_time::date, trending_date_parsed)
    end as days_since_publish,
    -- numeric snapshot measures (cumulative in source)
    views,
    likes,
    dislikes,
    comment_count,
    -- point-in-time rates using safe_divide.
    -- Denominator (views) can be 0 for very fresh uploads — NULL rather
    -- than divide-by-zero.
    {{ safe_divide('likes',       'views') }} as like_rate,
    {{ safe_divide('dislikes',    'views') }} as dislike_rate,
    {{ safe_divide('comment_count', 'views') }} as comment_rate,
    {{ safe_divide('likes + dislikes + comment_count', 'views') }} as engagement_rate,
    -- flag snapshots
    comments_disabled,
    ratings_disabled,
    video_error_or_removed,
    -- engagement metric is undefined when:
    --   - video_error_or_removed = true (data invalid)
    --   - ratings_disabled = true (likes/dislikes may be inaccurate)
    --   - views = 0 (denominator undefined)
    -- We expose has_valid_engagement so marts can opt-out cleanly.
    case
        when video_error_or_removed = true then false
        when ratings_disabled = true then false
        when views is null or views = 0 then false
        else true
    end as has_valid_engagement,
    -- tags (raw preserved; normalized + count derived via macro)
    tags_raw,
    {% set nt = normalize_tags('tags_raw') %}
    ({{ nt.normalized }}) as tags_normalized,
    ({{ nt.count }}) as tag_count,
    _source_file,
    _loaded_at
from joined
