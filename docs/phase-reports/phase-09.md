# Phase 9 — CI, Reproducibility, and GitHub Hygiene

## Files created
- `.github/workflows/dbt.yml`

## CI behavior
- Triggered on push/PR to `main`
- Python 3.12, Ubuntu latest
- Builds sample fixture (uses real category JSONs from `data/raw/` if
  present, else uses stub)
- Loads sample into `data/sample.duckdb`
- Runs `dbt deps`, `dbt seed`, `dbt build` (run + test), `dbt docs generate`
- Uploads `target/` as artifact on failure
- No Kaggle credentials required, no secrets in workflow

## Local reproducibility
```bash
make clean
make install
make validate-sample
make load-sample
make build
make test
```

Verified locally end-to-end.

## Conventional commit
`ci: add reproducible dbt build workflow`
