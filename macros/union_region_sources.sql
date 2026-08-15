{#  Union the 10 regional raw video tables into a single relation.
    Explicit allowlist — no dynamic discovery. #}
{% macro union_region_sources() %}
{% set regions = ['CA','DE','FR','GB','IN','JP','KR','MX','RU','US'] %}

{% for region in regions %}
    select
        cast('{{ region }}' as varchar) as region_code,
        cast(video_id as varchar)       as video_id,
        cast(trending_date as varchar)  as trending_date,
        cast(title as varchar)          as title,
        cast(channel_title as varchar)  as channel_title,
        cast(category_id as varchar)    as category_id,
        cast(publish_time as varchar)   as publish_time_raw,
        cast(tags as varchar)           as tags_raw,
        cast(views as bigint)           as views,
        cast(likes as bigint)           as likes,
        cast(dislikes as bigint)        as dislikes,
        cast(comment_count as bigint)   as comment_count,
        cast(thumbnail_link as varchar) as thumbnail_link,
        cast(comments_disabled as varchar)        as comments_disabled_raw,
        cast(ratings_disabled as varchar)         as ratings_disabled_raw,
        cast(video_error_or_removed as varchar)   as video_error_or_removed_raw,
        cast(description as varchar)             as description,
        cast(_source_file as varchar) as _source_file,
        cast(_loaded_at as timestamp) as _loaded_at
    from {{ source('youtube_raw', 'raw_youtube_videos__' ~ region) }}
    {% if not loop.last %}union all{% endif %}
{% endfor %}
{% endmacro %}
