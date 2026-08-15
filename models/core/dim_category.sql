-- Core dimension: one row per (region_code, category_id).
-- Source: staged categories. No dedup across regions.
select
    {{ dbt_utils.generate_surrogate_key(['region_code', 'category_id']) }} as category_key,
    region_code,
    category_id,
    category_title,
    category_channel_id,
    assignable
from {{ ref('stg_youtube_categories') }}
