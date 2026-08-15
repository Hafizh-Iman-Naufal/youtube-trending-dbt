# Phase 4 — Reusable Macros and Intermediate Logic

## Files created
- `macros/safe_divide.sql` — NULL for NULL/zero denominator
- `macros/normalize_tags.sql` — returns {normalized, count} via Jinja dict
- `models/intermediate/int_video_observations_enriched.sql` — joined obs + categories + rates
- `models/intermediate/int_video_lifecycle.sql` — per-(region,video) lifecycle aggregates
- `models/intermediate/_intermediate__models.yml`
- `docs/metric-definitions.md`
- `docs/phase-reports/phase-04.md` (this file)

## Commands
```bash
make load-sample
dbt seed --profiles-dir .
dbt build --profiles-dir . --select staging intermediate
# → sample: 132 tests PASS
DUCKDB_PATH=data/youtube.duckdb dbt seed --profiles-dir .
DUCKDB_PATH=data/youtube.duckdb dbt build --profiles-dir . --select staging intermediate
# → full: 136 tests PASS (361,311 enriched observations; 207,077 lifecycle rows)
```

## Macro behavior verified
- `safe_divide`: returns NULL on 0 denominator and NULL numerator
- `normalize_boolean`: handles `True`/`False`/`1`/`0`/`t`/`f`; NULL on unknown
- `normalize_tags`: returns `{normalized, count}` tuple via Jinja dict; preserves NULL/empty/`[none]`

## Decisions
- `safe_divide` returns NULL (not 0) — zero denominator is "undefined", not "zero"
- `has_valid_engagement` flag added in `int_video_observations_enriched`
  so marts can opt out cleanly when `video_error_or_removed=true`,
  `ratings_disabled=true`, or `views=0`
- `tag_count` derived via string length arithmetic (preserves raw tags
  without brittle split logic)
