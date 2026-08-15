# Phase 8 — Documentation, Lineage, and Portfolio Presentation

## Files created/modified
- `docs/lineage.md` — architecture diagram + commands
- `README.md` — full rewrite with final model inventory, quickstart,
  full-data setup, metrics, limitations, lineage instructions
- `docs/phase-reports/phase-08.md`

## dbt docs generation
```bash
make docs
# → target/manifest.json, target/catalog.json, target/index.html
```

The lineage graph at `docs/lineage.md` mirrors what `dbt docs serve`
renders interactively.

## Notes
- README quickstart verified against `make build` from clean checkout.
- Model inventory lists all 12 models (2 staging, 2 intermediate,
  4 core, 4 mart).
- No exposures added — no real downstream dashboard exists.
