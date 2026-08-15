-- Returns rows with negative cumulative measures.
-- Should be empty (Phase 0 confirmed zero negatives in source).
select region_code, video_id, trending_date, views, likes, dislikes, comment_count
from {{ ref('fct_video_trending_daily') }}
where
    views < 0
    or likes < 0
    or dislikes < 0
    or comment_count < 0
