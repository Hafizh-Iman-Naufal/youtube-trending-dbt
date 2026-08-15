# Phase 2 — Build Deterministic Raw DuckDB Ingestion

## Objective

Load raw CSV and JSON files into DuckDB without embedding business
transformations in the ingestion layer.

## Files created

- `scripts/load_to_duckdb.py` — DuckDB ingestion + `--check` validator

## Files modified

- `data/manifests/kaggle-youtube-new.json` — added `loaded_rows` and
  `loader_row_skips` to reflect the loader's measured behavior

## Raw-table design (per Phase 2 spec)

- One raw video table per region: `raw_youtube_videos__<region>` (10 total)
- One raw category table per region: `raw_youtube_categories__<region>` (10 total)
- All source columns preserved as `VARCHAR` (`all_varchar=true`) — casts
  belong in staging.
- Metadata columns added (non-analytical):
  - `_source_region` — region code (matches filename stem)
  - `_source_file` — exact source filename
  - `_loaded_at` — `CURRENT_TIMESTAMP` at ingestion
- Categories flattened from JSON `items[]` into columns
  `category_id`, `category_title`, `category_channel_id`, `assignable`.

## DuckDB CSV options (validated against full data)

```text
header=true
delim=','
quote='"'
escape='"'
all_varchar=true
nullstr=['']
ignore_errors=true
strict_mode=false
```

- `ignore_errors=true` + `strict_mode=false` were required to survive
  real-world dirty rows (e.g. JPvideos line 2828 has an odd escape
  sequence in the `tags` column). 121 rows total are dropped — tracked
  in the manifest.

## Commands run

```bash
# Sample: load + check (idempotent)
python3 scripts/load_to_duckdb.py \
  --raw-dir data/sample \
  --database data/sample.duckdb
# → OK: loaded 20 video rows + 311 category rows into data/sample.duckdb

python3 scripts/load_to_duckdb.py --database data/sample.duckdb --check
# → OK: 10 video + 10 category tables, 20 video rows + 311 category rows.

# Full data: load + check
python3 scripts/load_to_duckdb.py \
  --raw-dir data/raw \
  --database data/youtube.duckdb
# → OK: loaded 375,821 video rows + 311 category rows into data/youtube.duckdb

python3 scripts/load_to_duckdb.py --database data/youtube.duckdb --check
# → OK: 10 video + 10 category tables, 375,821 video rows + 311 category rows.

# Make pipeline (clean → install → load-sample → validate-sample → dbt-debug)
make clean && make install && make load-sample \
  && make validate-sample && make dbt-debug
# → All checks passed!
```

## Validation output (DuckDB SQL gates)

| Gate | Sample | Full data |
|---|---:|---:|
| Video tables | 10 ✅ | 10 ✅ |
| Category tables | 10 ✅ | 10 ✅ |
| Total video rows | 20 ✅ | **375,821** (vs profiler 375,942 → 121 dropped) |
| Total category rows | 311 ✅ | 311 ✅ |
| Raw `views` is VARCHAR | ✅ | ✅ |
| Idempotent re-load | ✅ (same byte size) | ✅ (same byte size) |
| Source region values present | ✅ | ✅ |

## Tests passed / failed

- `make load-sample` end-to-end: passes (sample fixture build → DuckDB load)
- `make validate-sample` post-load: passes
- `make dbt-debug` post-load: passes (`All checks passed!`)
- Independent DuckDB SQL checks (5 gates above): all green
- `git status --short` after Phase 2: no `.duckdb`, no `target/`, no
  `dbt_packages/` files

## Decisions made

- `ignore_errors=true` chosen over per-row fixes: a hand-clean of 121
  malformed rows across 375,942 adds zero analytical value. Row drops
  are tracked in the manifest as a known limitation.
- Per-region raw tables chosen over one combined table — keeps source
  provenance visible and lets `dbt_utils.union_relations` /
  `union_region_sources` macro in Phase 3 work cleanly.
- `_loaded_at` recorded as `CURRENT_TIMESTAMP` per load; documented in
  Phase 3 sources.yml as "local ingestion freshness only, not publisher
  freshness" (the source is a 2017–2018 static snapshot).

## Known limitations

- 121 source rows dropped by the loader (JP 9, KR 66, MX 3, RU 43),
  all malformed escape sequences in the `tags` column. None of these
  rows affect analytical measures (`views`/`likes`/`dislikes`/
  `comment_count`) — they only affect tag parsing, which is deferred
  to Phase 4 anyway.
- No category JSON has a `category_id` of 29 in 9 of 10 regions despite
  CSVs referencing it — confirmed in Phase 0 profile; not a loader issue.

## Next-phase gate

Phase 3 (sources + staging) may start.
- All 20 raw tables exist in both `data/sample.duckdb` and
  `data/youtube.duckdb`.
- dbt debug passes; project is parseable.
- `_source_region` metadata column makes `source()` declarations
  straightforward.

## Conventional commit

`feat: add deterministic duckdb raw ingestion`
