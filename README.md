# youtube-trending-dbt

A publishable dbt + DuckDB analytics engineering portfolio over the
[Kaggle `datasnaek/youtube-new`](https://www.kaggle.com/datasets/datasnaek/youtube-new)
dataset (CC0). Demonstrates dimensional modeling, source management,
custom macros, generic + singular tests, documentation, lineage,
reproducible local execution, and CI without external credentials.

## What this demonstrates

| Skill | Where |
|---|---|
| dbt sources, staging, intermediate, core, marts | `models/` |
| Dimensional modeling (grain, keys, snapshot vs delta metrics) | `models/core/`, `models/marts/` |
| Custom macros (safe_divide, normalize_boolean, normalize_tags) | `macros/` |
| Generic tests (`not_null`, `unique`, `accepted_values`, `relationships`) | `models/**/_*.yml` |
| Singular SQL tests (grain integrity, FK, date rules) | `tests/` |
| dbt docs + lineage | `dbt docs generate` |
| DuckDB ingestion, idempotent, no pandas | `scripts/load_to_duckdb.py` |
| Reproducible Make-driven workflow | `Makefile` |
| GitHub Actions CI using only tracked sample data | `.github/workflows/dbt.yml` |

## Dataset

- **Title:** Trending YouTube Video Statistics
- **Source:** <https://www.kaggle.com/datasets/datasnaek/youtube-new>
- **License:** CC0: Public Domain (dataset content)
- **Snapshot:** 2017-01-12 → 2018-06-31, 10 regions, ~375k observation rows
- **Repository code license:** see `LICENSE`
- **Full attribution and dataset/repo license separation:** `DATA_LICENSES.md`
- **Profile and checksums:** `docs/data-profile.md`, `data/manifests/`

## Repository layout

```text
youtube-trending-dbt/
├── .github/workflows/dbt.yml        # CI: sample-only build + test + docs
├── data/
│   ├── raw/                         # ignored; full Kaggle CSVs/JSONs
│   ├── sample/                      # tracked; small CI fixture
│   └── manifests/                   # tracked; checksums
├── docs/                            # data profile, decisions, phase reports
├── macros/                          # safe_divide, normalize_boolean, ...
├── models/{staging,intermediate,core,marts}/
├── seeds/region_metadata.csv        # region dimension seed
├── scripts/{validate_raw_files.py, profile_dataset.py,
│            load_to_duckdb.py, build_sample_fixture.py}
├── tests/                           # singular SQL data-quality tests
├── dbt_project.yml
├── packages.yml
├── profiles.yml
├── requirements.txt
├── Makefile
└── README.md
```

## Quickstart (sample data, no Kaggle needed)

```bash
git clone <this-repo>
cd youtube-trending-dbt
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make install            # alias for pip install -r requirements.txt
make validate-sample    # run the same validator against data/sample/
make load-sample        # load sample into data/sample.duckdb
make seed               # load region_metadata seed
make build              # dbt build (run + test) for everything
make test               # dbt test only
make docs               # generate dbt docs
```

## Full-data setup (Kaggle required)

1. Download `trending-youtube-video-stats.zip` from the Kaggle page
   above, or place your existing `trending_youtube_video_stats.zip`
   under `data/raw/`.
2. The validator and profiler expect the extracted files in `data/raw/`.
   If you have the ZIP, extract it there:

   ```bash
   unzip data/raw/trending_youtube_video_stats.zip -d data/raw/
   ```

3. Run the full pipeline:

   ```bash
   make validate-sample    # passes against data/raw/ as well
   python3 scripts/load_to_duckdb.py --raw-dir data/raw \
                                   --database data/youtube.duckdb
   DUCKDB_PATH=data/youtube.duckdb make build
   DUCKDB_PATH=data/youtube.duckdb make test
   ```

## Architecture

```text
Kaggle files
  ├── 10 regional video CSVs
  └── 10 regional category JSONs
          ↓
DuckDB raw tables
  ├── raw_youtube_videos__<region>
  └── raw_youtube_categories__<region>
          ↓
Sources (source freshness, source descriptions)
          ↓
Staging
  ├── stg_youtube_video_observations
  └── stg_youtube_categories
          ↓
Intermediate
  ├── int_video_observations_enriched
  └── int_video_lifecycle
          ↓
Core dimensional
  ├── dim_region
  ├── dim_category
  ├── dim_video
  └── fct_video_trending_daily
          ↓
Marts
  ├── mart_video_lifecycle
  ├── mart_channel_performance
  ├── mart_category_performance
  └── mart_regional_trending
```

## Model inventory (filled in by Phase 5+)

See `docs/data-model.md` after Phase 5.

## Metric definitions

See `docs/metric-definitions.md` after Phase 4.

## Limitations

- Source is a static 2017–2018 snapshot — no live data, no streaming.
- `channel_title` is a display label, not a durable channel key.
- Cumulative metrics (`views`/`likes`/`dislikes`/`comment_count`) are
  point-in-time snapshots in the source — never summed across days.

## Inspecting lineage and docs

```bash
dbt docs generate --profiles-dir . --target dev
dbt docs serve --profiles-dir . --host 127.0.0.1 --port 8080
```

Then open <http://127.0.0.1:8080>.
