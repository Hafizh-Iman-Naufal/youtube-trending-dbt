-- Returns rows where publication timestamp is clearly AFTER trending date
-- by more than 1 day. Tolerance of 1 day for timezone/UTC edge cases.
-- Phase 0 found ~19k raw violations but most were within timezone fuzz;
-- after tolerance, only true anomalies should remain.
select
    region_code,
    video_id,
    trending_date_parsed,
    publish_time,
    days_since_publish
from {{ ref('int_video_observations_enriched') }}
where days_since_publish is not null
  and days_since_publish < -1
