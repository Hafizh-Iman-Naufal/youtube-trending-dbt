-- Returns rows that duplicate the fact grain.
-- Should be empty on a successful load.
select
    observation_key,
    region_code,
    video_id,
    trending_date,
    count(*) as c
from {{ ref('fct_video_trending_daily') }}
group by 1, 2, 3, 4
having count(*) > 1
