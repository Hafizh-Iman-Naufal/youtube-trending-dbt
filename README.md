# youtube-trending-dbt

A publishable dbt + DuckDB analytics engineering portfolio over the
[Kaggle `datasnaek/youtube-new`](https://www.kaggle.com/datasets/datasnaek/youtube-new)
dataset (CC0). Demonstrates dimensional modeling, source management,
custom macros, generic + singular tests, documentation, lineage,
reproducible local execution, and CI without external credentials.

![dbt build](https://img.shields.io/badge/dbt-1.12.2-blue) ![duckdb](https://img.shields.io/badge/duckdb-1.5.5-green) ![python](https://img.shields.io/badge/python-%3E%3D3.12-blue)

## What this demonstrates

| Skill | Where |
|---|---|
| dbt sources, staging, intermediate, core, marts | `models/` |
| Dimensional modeling (grain, keys, snapshot vs delta metrics) | `models/core/`, `models/marts/` |
| Custom macros (`safe_divide`, `normalize_boolean`, `normalize_tags`, `union_region_sources`) | `macros/` |
| Generic tests (`not_null`, `unique`, `accepted_values`, `relationships`, `dbt_utils.unique_combination_of_columns`) | `models/**/_*.yml` |
| Singular SQL tests (grain integrity, FK, date rules) | `tests/` |
| dbt docs + lineage | `docs/lineage.md`, `make docs` |
| DuckDB ingestion, idempotent, no pandas | `scripts/load_to_duckdb.py` |
| Reproducible Make-driven workflow | `Makefile` |
| GitHub Actions CI using only tracked sample data | `.github/workflows/dbt.yml` |

## Dataset

- **Title:** Trending YouTube Video Statistics
- **Source:** <https://www.kaggle.com/datasets/datasnaek/youtube-new>
- **License:** CC0: Public Domain (dataset content)
- **Snapshot:** 2017-01-12 → 2018-06-31, 10 regions, ~375k observation rows
- **Repository code license:** MIT — see `LICENSE`
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
├── docs/                            # data profile, decisions, phase reports, lineage
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
├── LICENSE
├── DATA_LICENSES.md
└── README.md
```

## Quickstart (sample data, no Kaggle needed)

```bash
git clone <this-repo>
cd youtube-trending-dbt
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

make validate-sample    # run the same validator against data/sample/
make build-sample       # build sample fixture + seed + dbt build (everything)
make build-full         # load full data + seed + dbt build (everything)
make test               # dbt test only
make docs               # generate dbt docs
```

## Full-data setup (Kaggle required)

1. Download `trending-youtube-video-stats.zip` from the Kaggle page
   above, or place your existing `trending_youtube_video_stats.zip`
   under `data/raw/`.

2. Extract the archive into `data/raw/` (it should contain 10 regional
   `*videos.csv` files and 10 `*_category_id.json` files):

   ```bash
   unzip data/raw/trending_youtube_video_stats.zip -d data/raw/
   ```

3. Run the full pipeline:

   ```bash
   make build-full
   ```

## Architecture

```text
Kaggle files (10 CSVs + 10 JSONs)
        ↓
DuckDB raw tables (raw_youtube_videos__<region>, raw_youtube_categories__<region>)
        ↓
Sources (source freshness, source descriptions, source tests)
        ↓
Staging (stg_youtube_video_observations, stg_youtube_categories)
        ↓
Intermediate (int_video_observations_enriched, int_video_lifecycle)
        ↓
Core dimensional (dim_region, dim_category, dim_video, fct_video_trending_daily)
        ↓
Marts (mart_video_lifecycle, mart_channel_performance,
       mart_category_performance, mart_regional_trending)
```

See `docs/lineage.md` for the generated lineage graph.

## Model inventory

| Layer | Model | Grain |
|---|---|---|
| staging | `stg_youtube_video_observations` | `(region_code, video_id, trending_date)` |
| staging | `stg_youtube_categories` | `(region_code, category_id)` |
| intermediate | `int_video_observations_enriched` | `(region_code, video_id, trending_date)` |
| intermediate | `int_video_lifecycle` | `(region_code, video_id)` |
| core | `dim_region` | `region_code` |
| core | `dim_category` | `(region_code, category_id)` |
| core | `dim_video` | `(region_code, video_id)` |
| core | `fct_video_trending_daily` | `(region_code, video_id, trending_date)` |
| mart | `mart_video_lifecycle` | `(region_code, video_id)` |
| mart | `mart_channel_performance` | `(region_code, channel_title)` |
| mart | `mart_category_performance` | `(region_code, category_id, trending_date)` |
| mart | `mart_regional_trending` | `(region_code, trending_date)` |

## Metric definitions

See `docs/metric-definitions.md`. Snapshot measures
(`views`/`likes`/`dislikes`/`comment_count`) are point-in-time — never
sum across observations. Engagement rates are NULL when
`has_valid_engagement = false`.

## Limitations

- Source is a static 2017–2018 snapshot — no live data, no streaming.
- `channel_title` is a display label, not a durable channel key.
- `dim_video` carries the latest observation's metadata (representative
  current snapshot, not Type-2 history).
- 121 source rows skipped by loader (concentrated JP/KR/MX/RU with
  malformed escape sequences); see manifest.
- No causal virality / recommendation / cohort analysis — the dataset
  has no user-level data.

## Inspecting lineage and docs

```bash
make docs
dbt docs serve --profiles-dir . --host 127.0.0.1 --port 8080
```

Open <http://127.0.0.1:8080>.

## Phase reports

Each phase's evidence, commands, and decisions are recorded under
`docs/phase-reports/phase-XX.md`.
