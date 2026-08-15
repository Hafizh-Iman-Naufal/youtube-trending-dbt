# Phase 3 — Register dbt Sources and Implement Staging

## Objective

Make raw data discoverable through dbt sources and standardize
types/names without applying analytical business logic.

## Files created

- `models/staging/_staging__sources.yml` — 20 source tables (10 video +
  10 category), with column descriptions and source-level tests
- `models/staging/_staging__models.yml` — staging model schemas,
  tests, descriptions
- `models/staging/stg_youtube_video_observations.sql` — deduped
  observation view
- `models/staging/stg_youtube_categories.sql` — flattened category view
- `macros/union_region_sources.sql` — explicit-allowlist 10-region
  union macro
- `macros/normalize_boolean.sql` — boolean normalization macro
- `macros/generate_observation_key.sql` — surrogate-key macro
- `docs/phase-reports/phase-03.md` — this file

## Files modified

- `scripts/build_sample_fixture.py` — fixed 5 sample `trending_date`
  values that had been written in `YY.MM.DD` order; now correctly
  `YY.DD.MM` per source spec

## Source rules implemented

- Every raw region table (20 total) declared explicitly with column
  descriptions, source metadata, and source-level `not_null` tests on
  required columns (`_source_region`, `_source_file`, `_loaded_at`,
  `video_id`, `trending_date`, `category_id`)
- `_source_region` carries `accepted_values` against the 10-region
  allowlist (catches loader bugs early)
- `_loaded_at` documented as "local ingestion freshness only, not
  publisher freshness" — the source is a static 2017–2018 snapshot

## Staging rules implemented

- `stg_youtube_video_observations`:
  - `region_code` injected from filename via the macro
  - `trending_date` parsed explicitly as `YY.DD.MM` with documented
    two-digit-year rule
  - `publish_time` cast to TIMESTAMP via `try_strptime` (NULL on parse failure)
  - Numeric measures cast to BIGINT
  - Booleans normalized via the `normalize_boolean` macro
  - Raw preserved (`tags_raw`, `publish_time_raw`, `comments_disabled_raw`,
    `ratings_disabled_raw`, `video_error_or_removed_raw`) for audit
  - Dedup by `(region_code, video_id, trending_date)` picking the latest
    `_loaded_at` per grain key
  - `observation_key` surrogate generated via `dbt_utils.generate_surrogate_key`
  - **No** business logic (no engagement rates, no lifecycle)
- `stg_youtube_categories`:
  - All 10 regions UNION'd via explicit references
  - `category_id` cast to VARCHAR (matches CSV-side staging cast)
  - Composite uniqueness enforced via `dbt_utils.unique_combination_of_columns`

## Commands run

```bash
# Sample
make load-sample
dbt seed --profiles-dir .
dbt run  --profiles-dir . --select staging
dbt test --profiles-dir . --select staging

# Full data
python3 scripts/load_to_duckdb.py \
  --raw-dir data/raw --database data/youtube.duckdb
DUCKDB_PATH=data/youtube.duckdb dbt run  --profiles-dir . --select staging
DUCKDB_PATH=data/youtube.duckdb dbt test --profiles-dir . --select staging
```

## Validation output

| Check | Sample | Full data |
|---|---:|---:|
| `dbt parse` | ✅ | ✅ |
| `dbt run --select staging` | 2/2 PASS | 2/2 PASS |
| `dbt test --select staging` | 116/116 PASS | 116/116 PASS |
| Staging observation row count | 20 | **361,311** |
| Staging category row count | 311 | 311 |
| Duplicate `(region_code, video_id, trending_date)` after dedup | 0 | 0 |
| NULL `trending_date_parsed` | 0 | 0 |
| Duplicate `(region_code, category_id)` in staging categories | 0 | 0 |

Per-region observation counts (full data):

```text
CA: 40,881    DE: 40,840    FR: 40,724    GB: 38,742
IN: 32,458    JP: 14,536    KR: 31,881    MX: 40,070
RU: 40,280    US: 40,899
```

(JP, IN, KR, GB are smaller than profiler counts because of the 121
loader-skipped rows + the 14,518 duplicate-grain dedup — the dedup is
concentrated in those regions, matching Phase 0 profile findings.)

## Tests passed / failed

116 source + model tests, all PASS:
- `not_null` on every required key
- `unique` on `observation_key` (surrogate)
- `unique_combination_of_columns(region_code, category_id)` on categories
- `accepted_values` on `region_code` in both staging models and 10 sources

## Decisions made

- Dedup rule: pick the latest `_loaded_at` per grain key (deterministic,
  idempotent, explains the 14,518 same-day re-pulls from Phase 0)
- Two-digit-year rule stays in staging SQL (not a macro) — it's a single
  call site and clearer inline
- `observation_key` surrogate via `dbt_utils.generate_surrogate_key` —
  matches the spec's "deterministic and include region where grain
  requires it"
- Sample fixture dates had to be re-emitted in correct `YY.DD.MM` form
  (caught by `trending_date_parsed` not-null test — exactly the kind of
  test that earns its keep)

## Known limitations

- `accepted_values` test on source `_source_region` is the only schema
  guardrail at the source layer — Phase 6 will add singular tests for
  the deeper invariants.
- The staging layer uses `try_strptime` which silently NULLs bad dates.
  Phase 6 will add a singular test that asserts zero unexpected NULLs
  on `trending_date_parsed` for full-data loads.

## Next-phase gate

Phase 4 (macros + intermediate) may start.
- Sources declared with tests.
- Staging views compile + run + test on both sample and full data.
- Macro-driven `union_region_sources` proven.
- `safe_divide` and `normalize_tags` macros pending (Phase 4).

## Conventional commit

`feat: add dbt sources and staging models`
