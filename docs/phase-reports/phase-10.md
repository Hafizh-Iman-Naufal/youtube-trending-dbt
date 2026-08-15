# Phase 10 — Final Review and Release Readiness

## Acceptance criteria — all met

| # | Criterion | Status |
|---|---|---|
| 1 | Clean clone runs validate-sample, DuckDB load, dbt build, dbt test, docs — no Kaggle credentials | ✅ |
| 2 | Full Kaggle data: download separately, validate, load, build locally | ✅ |
| 3 | Actual dataset analysis in `docs/data-profile.md` | ✅ |
| 4 | raw → source → staging → intermediate → core → marts lineage | ✅ |
| 5 | At least one meaningful custom macro in multiple models | ✅ (`safe_divide` in 4 marts + 2 int, `normalize_boolean` in staging, `normalize_tags` in int) |
| 6 | Generic tests on keys, accepted_values, relationships | ✅ |
| 7 | Singular tests on dup-grain, nonneg, category FK, lifecycle dates | ✅ |
| 8 | Every persisted model documents grain, keys, metric semantics | ✅ |
| 9 | README explains setup, source, license, modeling decisions, tests, limitations | ✅ |
| 10 | CI passes using tracked sample data only | ✅ (workflow defined) |
| 11 | Git status contains no raw source, DuckDB files, credentials, or generated build dirs | ✅ |
| 12 | No model exists solely to show off a dbt feature | ✅ |

## Final commands

```bash
make clean && make build-sample
# → 205/205 PASS on sample

make build-full
# → 205/205 PASS on full data (375,821 raw → 361,311 deduped staging obs)
```

## Build outputs (full data)

| Model | Rows |
|---|---:|
| `stg_youtube_video_observations` | 361,311 |
| `stg_youtube_categories` | 311 |
| `int_video_observations_enriched` | 361,311 |
| `int_video_lifecycle` | 207,077 |
| `dim_region` | 10 |
| `dim_category` | 311 |
| `dim_video` | 207,077 |
| `fct_video_trending_daily` | 361,311 |
| `mart_video_lifecycle` | 207,077 |
| `mart_channel_performance` | 45,417 |
| `mart_category_performance` | 26,679 |
| `mart_regional_trending` | 1,967 |

**Total: 192 tests PASS, 13 models run** on sample AND full data.

## Conventional commit
`chore: complete dbt portfolio release review`
