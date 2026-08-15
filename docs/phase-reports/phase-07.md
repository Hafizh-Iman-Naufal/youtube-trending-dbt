# Phase 7 — Build Analytical Marts

## Files created
- `models/marts/mart_video_lifecycle.sql` — grain: (region_code, video_id)
- `models/marts/mart_channel_performance.sql` — grain: (region_code, channel_title)
- `models/marts/mart_category_performance.sql` — grain: (region_code, category_id, trending_date)
- `models/marts/mart_regional_trending.sql` — grain: (region_code, trending_date)
- `models/marts/_marts__models.yml`
- `docs/phase-reports/phase-07.md`

## Commands
```bash
dbt build --profiles-dir . --select marts                       # sample → 23/23
DUCKDB_PATH=data/youtube.duckdb dbt build --profiles-dir . --select marts  # full → 23/23
```

## Mart row counts (full data)
- `mart_video_lifecycle`: **207,077** rows
- `mart_channel_performance`: **45,417** rows
- `mart_category_performance`: **26,679** rows
- `mart_regional_trending`: **1,967** rows

## Decisions
- `mart_video_lifecycle` reads directly from `int_video_lifecycle`
  (no fact join needed; lifecycle is already aggregated).
- `mart_channel_performance` joins fact + lifecycle for `latest_views`/
  `peak_views` per video, then aggregates per channel label. Documented
  that `channel_title` is a display label, not a FK.
- `mart_category_performance` uses daily grain for time-series
  consumption; `mart_regional_trending` uses the same.
- All rate metrics are wrapped in `CASE WHEN has_valid_engagement` to
  honor the validity flag from Phase 4.
