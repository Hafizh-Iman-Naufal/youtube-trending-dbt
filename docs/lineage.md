# Lineage

```text
seeds/region_metadata.csv
        │
        ▼
   dim_region
        │
        │
raw_youtube_videos__<region> (×10)   raw_youtube_categories__<region> (×10)
        │                                       │
        ▼                                       ▼
stg_youtube_video_observations     stg_youtube_categories
        │                                       │
        └────────────┬──────────────────────────┘
                     ▼
        int_video_observations_enriched ──── int_video_lifecycle
                     │                              │
                     ▼                              ▼
        dim_video  ←────  fct_video_trending_daily
                              │
        �─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  mart_video_lifecycle  mart_channel_performance  mart_category_performance  mart_regional_trending
```

## Generated docs

```bash
dbt docs generate --profiles-dir . --target dev
dbt docs serve --profiles-dir . --host 127.0.0.1 --port 8080
```

Open <http://127.0.0.1:8080> for the interactive lineage graph.

## CI badge

After Phase 9 lands `.github/workflows/dbt.yml`, the README will display
the workflow status badge pointing at the run history.
