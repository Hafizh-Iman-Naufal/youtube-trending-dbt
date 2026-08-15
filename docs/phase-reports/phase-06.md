# Phase 6 — Data Quality Tests

## Files created
- `tests/assert_no_duplicate_observations.sql`
- `tests/assert_nonnegative_measures.sql`
- `tests/assert_category_reference_integrity.sql`
- `tests/assert_publish_before_trending.sql`
- `tests/assert_lifecycle_dates.sql`
- `docs/metric-definitions.md`
- `docs/phase-reports/phase-06.md`

## Commands
```bash
make load-sample && dbt seed --profiles-dir .
dbt build --profiles-dir . --select staging intermediate core  # sample → 176/176
DUCKDB_PATH=data/youtube.duckdb dbt seed --profiles-dir .
DUCKDB_PATH=data/youtube.duckdb dbt build --profiles-dir . --select staging intermediate core  # full → 176/176
```

## Severity policy
- **error**: dup-grain, nonneg-measures, category FK (excluding cat 29),
  lifecycle dates
- **warn** (via `has_valid_engagement` flag, not test failure): videos
  with `video_error_or_removed=true`, `ratings_disabled=true`,
  `views=0`
- **info**: source freshness — not asserted (static snapshot)

## Bug caught by tests
Sample row `vIN00002` originally had publish_time after trending_date
(2018-05-01 publish, 2018-01-05 trending) — caught by
`assert_publish_before_trending` after introducing 1-day tolerance for
UTC timezone fuzz. Fixed in `build_sample_fixture.py`.
