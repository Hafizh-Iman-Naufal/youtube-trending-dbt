# youtube-trending-dbt Makefile
# Run `make help` for the target list.

DBT      ?= dbt
PYTHON   ?= python3
DB_PATH  ?= data/sample.duckdb
PROFILES ?= --profiles-dir .
RAW_DIR  ?= data/sample
SAMPLE_DIR ?= data/sample

.PHONY: help install validate-sample load-sample dbt-debug dbt-deps seed build test docs clean

help: ## list available targets
	@awk 'BEGIN{FS=":.*##"; printf "\nTargets:\n"} /^[a-zA-Z_-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## install pinned python deps
	$(PYTHON) -m pip install -r requirements.txt

validate-sample: ## run stdlib structural validator against $(SAMPLE_DIR)
	$(PYTHON) scripts/validate_raw_files.py --raw-dir $(SAMPLE_DIR)

load-sample: ## build sample fixture and load into DuckDB
	$(PYTHON) scripts/build_sample_fixture.py --out-dir $(SAMPLE_DIR) --from-raw data/raw
	$(PYTHON) scripts/load_to_duckdb.py --raw-dir $(SAMPLE_DIR) --database $(DB_PATH)

dbt-deps: ## install dbt package deps
	$(DBT) deps $(PROFILES)

dbt-debug: ## run dbt debug
	$(DBT) debug $(PROFILES)

seed: ## load region_metadata seed (runs dbt deps first)
	$(DBT) deps $(PROFILES)
	$(DBT) seed $(PROFILES)

build: ## dbt build (run + test) full project (runs dbt deps first)
	$(DBT) deps $(PROFILES)
	$(DBT) build $(PROFILES)

test: ## dbt test only (runs dbt deps first)
	$(DBT) deps $(PROFILES)
	$(DBT) test $(PROFILES)

docs: ## generate dbt docs
	$(DBT) deps $(PROFILES)
	$(DBT) docs generate $(PROFILES)

clean: ## remove generated artifacts
	rm -rf target logs dbt_packages
	rm -f data/*.duckdb data/*.duckdb.wal
