# Phase 5 — Build Core Dimensional Models

## Files created
- `models/core/dim_region.sql`, `dim_category.sql`, `dim_video.sql`, `fct_video_trending_daily.sql`
- `models/core/_core__models.yml`
- `docs/data-model.md`
- `docs/phase-reports/phase-05.md`

## Commands run
```bash
dbt build --profiles-dir . --select core                    # sample → 35/35 PASS
DUCKDB_PATH=data/youtube.duckdb dbt seed --profiles-dir .   # seeds into full db
DUCKDB_PATH=data/youtube.duckdb dbt build --profiles-dir . --select core  # full → 35/35 PASS
```

## Validation
| Check | Sample | Full |
|---|---:|---:|
| Run core models | 4/4 ✅ | 4/4 ✅ |
| Generic tests | 31/31 ✅ | 31/31 ✅ |

`fct_video_trending_daily` has zero duplicate `observation_key`,
`region_key`/`video_key`/`category_key` relationships all pass.

## Decisions
- `dim_video` picks latest observation per (region_code, video_id) for
  representative metadata (no Type-2 history).
- No `dim_channel` — `channel_title` is display label only.
- No snapshots — static 2017–2018 source.
- `table` materialization for fact, `view` for staging/intermediate (per
  dbt_project.yml).
