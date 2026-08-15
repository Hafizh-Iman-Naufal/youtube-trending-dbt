-- Staging model: one row per (region_code, video_id, trending_date) observation.
-- Casts source VARCHAR → typed columns. Does NOT apply business logic.

with source as (

    {{ union_region_sources() }}

),

dedup as (
    -- 14.5k duplicate-grain rows exist (concentrated in IN/JP/KR) —
    -- likely same-day re-pulls. Pick the latest _loaded_at per grain key.
    select *
    from source
    qualify row_number() over (
        partition by region_code, video_id, trending_date
        order by _loaded_at desc
    ) = 1
)

select
    -- grain
    region_code,
    video_id,
    trending_date,
    -- parsed trending date: 'YY.DD.MM' (two-digit-year rule: 00-69 -> 20xx, 70-99 -> 19xx)
    case
        when trending_date is null then null
        when not regexp_matches(trending_date, '^[0-9]{2}\.[0-9]{2}\.[0-9]{2}$') then null
        else
            try_strptime(
                case
                    when cast(substr(trending_date, 1, 2) as integer) < 70
                        then '20' || substr(trending_date, 1, 2) || '-' ||
                             substr(trending_date, 7, 2) || '-' ||
                             substr(trending_date, 4, 2)
                    else '19' || substr(trending_date, 1, 2) || '-' ||
                         substr(trending_date, 7, 2) || '-' ||
                         substr(trending_date, 4, 2)
                end,
                '%Y-%m-%d'
            )::date
    end as trending_date_parsed,
    title,
    channel_title,
    category_id,
    -- parsed publish timestamp (UTC). Tolerate nulls/odd values.
    case
        when publish_time_raw is null or publish_time_raw = '' then null
        else try_strptime(publish_time_raw, '%Y-%m-%dT%H:%M:%S.%fZ')::timestamp
    end as publish_time,
    publish_time_raw,
    -- raw tags (preserved)
    tags_raw,
    -- numeric measures (cumulative snapshots in source)
    views,
    likes,
    dislikes,
    comment_count,
    thumbnail_link,
    -- normalized booleans
    {{ normalize_boolean('comments_disabled_raw') }}        as comments_disabled,
    {{ normalize_boolean('ratings_disabled_raw') }}         as ratings_disabled,
    {{ normalize_boolean('video_error_or_removed_raw') }}   as video_error_or_removed,
    -- preserve raw for audit
    comments_disabled_raw,
    ratings_disabled_raw,
    video_error_or_removed_raw,
    description,
    -- metadata
    _source_file,
    _loaded_at,
    -- deterministic surrogate key for downstream FKs
    {{ generate_observation_key() }} as observation_key

from dedup
