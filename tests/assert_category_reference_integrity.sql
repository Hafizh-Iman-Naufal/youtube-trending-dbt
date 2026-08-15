-- Returns staged observations without a category match on
-- (region_code, category_id). Phase 0 found category 29 missing
-- from JSONs for 9 regions — expected orphans.
-- This test excludes that known case.
select o.region_code, o.video_id, o.trending_date, o.category_id
from {{ ref('stg_youtube_video_observations') }} o
left join {{ ref('stg_youtube_categories') }} c
    on o.region_code = c.region_code and o.category_id = c.category_id
where c.category_id is null
  and not (o.category_id = '29')
