# Data Model

> dbt project structure: `models/staging/` → `models/intermediate/` → `models/core/` → `models/marts/`.

## Sources (20 tables)

| Source table | Rows (full) | Purpose |
|---|---:|---|
| `raw_youtube_videos__<region>` × 10 | 375,821 | One per region, all VARCHAR |
| `raw_youtube_categories__<region>` × 10 | 311 | Flattened from JSON |

All measure columns are `VARCHAR` at this layer (casts in staging).

## Staging (2 views)

| Model | Grain | Rows (full) |
|---|---|---:|
| `stg_youtube_video_observations` | `(region_code, video_id, trending_date)` | 361,311 (after dedup) |
| `stg_youtube_categories` | `(region_code, category_id)` | 311 |

Dedup picks the latest `_loaded_at` per grain key — eliminates the
14,518 same-day re-pulls found by Phase 0 profiling.

## Intermediate (2 views)

| Model | Grain | Rows (full) |
|---|---|---:|
| `int_video_observations_enriched` | observation | 361,311 |
| `int_video_lifecycle` | `(region_code, video_id)` | 207,077 |

Enrichment adds category title + engagement rates (NULL when
`has_valid_engagement=false`). Lifecycle aggregates per-video-region
(first/last trending date, peak/latest snapshot measures).

## Core (3 dims + 1 fact)

| Model | Grain | Rows (full) |
|---|---|---:|
| `dim_region` | `region_code` | 10 |
| `dim_category` | `(region_code, category_id)` | 311 |
| `dim_video` | `(region_code, video_id)` | 207,077 |
| `fct_video_trending_daily` | `(region_code, video_id, trending_date)` | 361,311 |

`dim_video` carries the **latest** observation's metadata
(title/channel/publish_time) — representative current snapshot, not a
Type-2 history.

`fct_video_trending_daily` carries surrogate FKs to the three dims plus
all snapshot measures and derived rates.

## Marts (4 tables — Phase 7)

See `models/marts/` after Phase 7.

## Decisions

See `docs/modeling-decisions.md`.
