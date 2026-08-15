# Phase 0 — Acquire, Inspect, and Profile Dataset

## Objective

Establish evidence-based schema, grain, quality findings, and source
manifest before choosing final dbt models.

## Files created

- `scripts/validate_raw_files.py` — stdlib structural validator
- `scripts/profile_dataset.py` — stdlib profiler (csv + json only)
- `docs/data-profile.md` — measured profile output
- `docs/modeling-decisions.md` — Phase 0 decisions and open questions
- `data/manifests/kaggle-youtube-new.json` — source/archive/file checksums
- `DATA_LICENSES.md` — dataset + repo license split

## Files modified

- none

## Commands run

```bash
# Validation (stdlib, ~10s)
python3 scripts/validate_raw_files.py \
  --raw-dir data/raw \
  --json-out data/manifests/validate_raw_files.json
# → OK: 10 CSVs (539,139,311 bytes), 10 JSONs (81,579 bytes).
#   All 20 expected files present with correct schema.

# Profile (stdlib, ~60s on full 539MB)
python3 scripts/profile_dataset.py \
  --raw-dir data/raw \
  --output docs/data-profile.md
# → Profiled 10 CSVs, 10 JSONs, 375,942 total rows.

# Manifest JSON sanity
python3 -m json.tool data/manifests/kaggle-youtube-new.json
# → valid JSON, sha256 for archive + each file
```

## Validation output summary

- 10 expected regional CSV files, 10 expected category JSON files. No
  missing or extra entries.
- CSV headers match the observed 16-column schema byte-for-byte.
- JSON top-level shape is `{ "items": [ { "id", "snippet": {...} } ] }`
  for every region.
- File encoding: most files decode as UTF-8; some contain isolated
  non-UTF-8 byte sequences, in which case the scripts transparently
  fall back to latin-1 (and the profile reports zero type-parse failures).

## Tests / checks passed

| Check | Result |
|---|---|
| Exactly 20 expected source files | ✅ |
| All CSV headers match expected 16-column schema | ✅ |
| All JSON top-level structure valid | ✅ |
| Profiler row counts (10 CSVs summed) | 375,942 |
| Profile report rendered to `docs/data-profile.md` | ✅ |
| Manifest validates as JSON | ✅ |

## Measurements (full data)

- 375,942 rows across 10 regions
- 361,424 distinct `(region, video_id, trending_date)` keys
- 14,518 duplicate-grain rows (concentrated: IN 4,894, JP 5,980, KR 2,625)
- 12,570 exact-duplicate rows
- 66,449 videos appear in 2+ regions
- Date range per region: `2017-01-12` → `2018-06-31` (DD > MM in source)
- 0 type-parse failures across all numeric/date/timestamp/boolean columns
- 0 negative values in any cumulative measure
- `video_error_or_removed = true`: 253 rows (excluded from engagement calcs)
- Category `29` referenced by 9/10 regions but absent from every JSON

## Decisions made

- See `docs/modeling-decisions.md` (D1–D10) — fact grain, no `dim_channel`,
  cumulative metrics are snapshots, two-digit-year rule, severity
  policies, no snapshots, no incremental.

## Known limitations

- Profile is stdlib-only; deeper DuckDB-side quality checks (NULL counts
  per region, percentile distributions, exact-dup dedup keying) move to
  Phase 2 ingestion.
- Tag delimiter parsing deferred to Phase 4.
- `trending_date` two-digit year boundary (00–69 vs 70–99) is documented
  but not asserted by a test — Phase 6 will add a singular test.

## Next-phase gate

Phase 1 (Scaffold Repository and Reproducible Tooling) may start.
All Phase 1 prerequisites (Python 3.11+ available, DuckDB installable
via pip, dbt-duckdb installable) are confirmed against the current
environment.

## Conventional commit

`docs: add dataset profile and source manifest`
