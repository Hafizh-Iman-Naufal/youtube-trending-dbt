# Phase 1 — Scaffold Repository and Reproducible Tooling

## Objective

Create a clean GitHub-ready project skeleton that runs against a small
fixture without Kaggle access.

## Files created

- `README.md` — quickstart, architecture, model inventory, limitations
- `LICENSE` — MIT for the repository code (dataset stays CC0)
- `Makefile` — `install`, `validate-sample`, `load-sample`, `dbt-deps`,
  `dbt-debug`, `seed`, `build`, `test`, `docs`, `clean`, `help`
- `requirements.txt` — Python deps pinned
- `profiles.yml` — committed, no secrets; reads `DUCKDB_PATH` env var
- `dbt_project.yml` — dbt 1.12-compatible config
- `packages.yml` — pinned `dbt_utils >=1.1.0,<2.0.0`
- `seeds/region_metadata.csv` — 10-row region dimension seed
- `seeds/_seeds.yml` — region_metadata schema + tests
- `scripts/build_sample_fixture.py` — deterministic sample fixture
  builder, copies real category JSONs from `data/raw/` for category
  joins to work end-to-end
- `sample.env.example` — sample env template
- `docs/phase-reports/phase-01.md` — this file

## Files modified

- `.gitignore` — added `.user.yml` and `package-lock.yml` (dbt local
  artifacts); confirmed everything else stays ignored

## Pinned versions

| Package | Version | Source |
|---|---|---|
| `dbt-core` | `1.12.2` | latest stable (pip index) |
| `dbt-duckdb` | `1.11.0` | latest compatible with dbt-core 1.12 |
| `duckdb` | `1.5.5` | bundled by dbt-duckdb 1.11 |
| `dbt_utils` | `>=1.1.0,<2.0.0` (resolved to 1.4.1) | dbt package manager |

Python: project supports **>=3.12** (per requirement). Tested locally
against Python 3.11.15 (Hermes env), which dbt 1.12 also supports.

## Commands run

```bash
# Install pinned deps
make install
# → dbt-core-1.12.2, dbt-duckdb-1.11.0, duckdb-1.5.5 installed

# Build sample fixture (idempotent)
python3 scripts/build_sample_fixture.py --out-dir data/sample --from-raw data/raw
# → OK: wrote 10 CSVs and 10 JSONs under data/sample

# Validate the fixture with the same structural validator as full data
make validate-sample
# → OK: 10 CSVs (5,908 bytes), 10 JSONs (81,579 bytes).

# dbt debug
make dbt-debug
# → All checks passed!

# dbt deps + parse (after deps)
dbt deps --profiles-dir .
dbt parse --profiles-dir .
# → Installed dbt-labs/dbt_utils 1.4.1; parse OK
#   (warning about unused config paths is expected — stages come in later phases)
```

## Validation output

| Check | Result |
|---|---|
| Fresh install (`make install`) | ✅ |
| Sample fixture validates with same validator as full data | ✅ |
| `dbt debug --profiles-dir .` | ✅ All checks passed |
| `dbt parse --profiles-dir .` | ✅ (with `dbt deps` first) |
| No raw data, DuckDB, `.venv`, `target/`, `logs/`, `dbt_packages/` in `git status` | ✅ |

`git status --short` after Phase 1 (clean working tree, sample
committed, raw/duckdb/target gitignored):

```text
?? LICENSE
?? Makefile
?? README.md
?? data/sample/
?? dbt_project.yml
?? packages.yml
?? profiles.yml
?? requirements.txt
?? sample.env.example
?? scripts/build_sample_fixture.py
?? seeds/
```

## Tests passed / failed

- `dbt seed` on `region_metadata`: `not_null` + `unique` on
  `region_code` will activate in Phase 3 once `dbt build` can find
  them (already wired in `seeds/_seeds.yml`).
- All other tests deferred to Phase 6.

## Decisions made

- Sample fixture uses real category JSONs from `data/raw/` so category
  joins work in CI without re-curating ~30 categories per region. CSVs
  are tiny hand-curated slices with all flag combinations present.
- `dbt-utils` pinned to `>=1.1.0,<2.0.0` for `surrogate_key`/`expression_is_true`
  helpers used in later phases.
- `dbt-target-path` removed (deprecated in dbt 1.12+).
- `package-lock.yml` and `.user.yml` gitignored (dbt local state).

## Known limitations

- `make build` will fail until Phase 3+ defines staging models — the
  current target only has a region seed.
- The sample fixture is intentionally tiny (2 rows per region). It
  exists to validate schema and code paths, not to demo realistic
  metric distributions.
- Python env in use is 3.11.15; downstream users on `>=3.12` will
  work identically.

## Next-phase gate

Phase 2 (DuckDB ingestion) may start.
- `dbt-core` + `dbt-duckdb` + `duckdb` are installed.
- Sample fixture exists.
- Project loads (`dbt parse` clean).

## Conventional commit

`chore: scaffold reproducible dbt duckdb project`
