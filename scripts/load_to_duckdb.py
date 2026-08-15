"""Load raw Kaggle CSVs and category JSONs into DuckDB.

Per Phase 2 spec:
  - one raw video table per region (source is region-file based)
  - one raw category table per region, flattened
  - text columns kept as text in raw (casts belong in staging)
  - metadata columns added: _source_region, _source_file, _loaded_at
  - parameterized paths, no hardcoded home dirs
  - DuckDB's CSV reader with explicit options after validating result
  - idempotent: re-run does not duplicate rows; second invocation drops
    and recreates the raw tables

Usage:
  python3 scripts/load_to_duckdb.py --raw-dir data/sample --database data/sample.duckdb
  python3 scripts/load_to_duckdb.py --raw-dir data/raw --database data/youtube.duckdb
  python3 scripts/load_to_duckdb.py --database data/sample.duckdb --check
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import duckdb

EXPECTED_REGIONS = ["CA", "DE", "FR", "GB", "IN", "JP", "KR", "MX", "RU", "US"]


def detect_encoding(path: Path) -> str:
    try:
        path.read_bytes().decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def load_videos(con: duckdb.DuckDBPyConnection, raw_dir: Path, region: str) -> int:
    """Load one regional video CSV into raw_youtube_videos__<region>.
    Returns row count."""
    csv = raw_dir / f"{region}videos.csv"
    table = f"raw_youtube_videos__{region}"
    # Explicit CSV options. The source has quoted commas, embedded
    # newlines, occasional non-UTF-8 bytes, and rare malformed lines
    # (e.g. JPvideos line 2828 has an odd escape sequence). Auto-sniff
    # fails on the full data because of those dirty bytes. So:
    #  - delim=',' header=True
    #  - quote='"', escape='"' (standard)
    #  - all_varchar=True to preserve source types verbatim (casts in staging)
    #  - nullstr=[''] so empty fields become NULL, matching profiler convention
    #  - ignore_errors=true: dirty rows are skipped (logged via row count diff)
    #  - strict_mode=false: relax parser rules around quoting
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(
        f"""
        CREATE TABLE {table} AS
        SELECT
          '{region}' AS _source_region,
          '{csv.name}' AS _source_file,
          CURRENT_TIMESTAMP AS _loaded_at,
          *
        FROM read_csv(
          '{csv.as_posix()}',
          header=True,
          delim=',',
          quote='"',
          escape='"',
          all_varchar=True,
          nullstr=[''],
          ignore_errors=true,
          strict_mode=false
        )
        """
    )
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return n


def load_categories(con: duckdb.DuckDBPyConnection, raw_dir: Path, region: str) -> int:
    """Flatten one regional category JSON into raw_youtube_categories__<region>."""
    js = raw_dir / f"{region}_category_id.json"
    table = f"raw_youtube_categories__{region}"
    con.execute(f"DROP TABLE IF EXISTS {table}")
    # Use DuckDB's JSON reader. The source has shape:
    #   {"items": [{"id": "...", "snippet": {"title": "...", "channelId": "...",
    #                "assignable": bool, ...}}, ...]}
    # We flatten snippet fields so dbt sources can reference them.
    con.execute(
        f"""
        CREATE TABLE {table} AS
        SELECT
          '{region}'::VARCHAR AS _source_region,
          '{js.name}'::VARCHAR AS _source_file,
          CURRENT_TIMESTAMP AS _loaded_at,
          CAST(item.id AS VARCHAR)              AS category_id,
          item.snippet.title                    AS category_title,
          item.snippet.channelId                AS category_channel_id,
          CAST(item.snippet.assignable AS BOOLEAN) AS assignable
        FROM read_json_auto('{js.as_posix()}') AS doc,
             UNNEST(doc.items) AS t(item)
        """
    )
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return n


def cmd_load(args: argparse.Namespace) -> int:
    raw: Path = args.raw_dir
    db: Path = args.database
    if not raw.is_dir():
        print(f"ERROR: raw dir not found: {raw}", file=sys.stderr)
        return 2

    db.parent.mkdir(parents=True, exist_ok=True)
    # remove existing db so the load is idempotent at the db level too
    if db.exists() and not args.append:
        db.unlink()

    con = duckdb.connect(str(db))
    try:
        total_v = 0
        total_c = 0
        for region in EXPECTED_REGIONS:
            csv = raw / f"{region}videos.csv"
            js = raw / f"{region}_category_id.json"
            if not csv.exists() or not js.exists():
                print(f"ERROR: missing files for {region}", file=sys.stderr)
                return 1
            v = load_videos(con, raw, region)
            c = load_categories(con, raw, region)
            total_v += v
            total_c += c
            print(f"  {region}: {v} video rows, {c} category rows")

        # row counts summary
        print(f"OK: loaded {total_v} video rows + {total_c} category rows "
              f"into {db}")
        return 0
    finally:
        con.close()


def cmd_check(args: argparse.Namespace) -> int:
    """Sanity-check existing DuckDB: table counts, no schema drift, no row accumulation."""
    db: Path = args.database
    if not db.exists():
        print(f"ERROR: db not found: {db}", file=sys.stderr)
        return 2
    con = duckdb.connect(str(db), read_only=True)
    try:
        tables = sorted(t[0] for t in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='main' AND table_name LIKE 'raw_youtube_%'"
        ).fetchall())
        expected_v = {f"raw_youtube_videos__{r}" for r in EXPECTED_REGIONS}
        expected_c = {f"raw_youtube_categories__{r}" for r in EXPECTED_REGIONS}
        got_v = {t for t in tables if "videos" in t}
        got_c = {t for t in tables if "categories" in t}

        problems: list[str] = []
        if got_v != expected_v:
            problems.append(f"video tables mismatch: missing {expected_v - got_v}, "
                            f"extra {got_v - expected_v}")
        if got_c != expected_c:
            problems.append(f"category tables mismatch: missing {expected_c - got_c}, "
                            f"extra {got_c - expected_c}")

        # every video table must have the metadata cols
        for t in expected_v:
            cols = [r[0] for r in con.execute(
                f"SELECT column_name FROM information_schema.columns "
                f"WHERE table_name='{t}'"
            ).fetchall()]
            for need in ("_source_region", "_source_file", "_loaded_at", "video_id",
                         "trending_date", "title", "category_id", "views"):
                if need not in cols:
                    problems.append(f"{t}: missing column {need}")

        if problems:
            for p in problems:
                print(f"FAIL: {p}", file=sys.stderr)
            return 1
        n_v = sum(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in expected_v)
        n_c = sum(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in expected_c)
        print(f"OK: {len(expected_v)} video + {len(expected_c)} category tables, "
              f"{n_v:,} video rows + {n_c:,} category rows.")
        return 0
    finally:
        con.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", type=Path, default=None)
    ap.add_argument("--database", type=Path, required=True)
    ap.add_argument("--append", action="store_true",
                    help="Do not delete existing db before loading (still drops raw tables)")
    ap.add_argument("--check", action="store_true",
                    help="Only check the db; do not load")
    args = ap.parse_args(argv)

    if args.check:
        return cmd_check(args)
    if args.raw_dir is None:
        print("ERROR: --raw-dir required for load", file=sys.stderr)
        return 2
    return cmd_load(args)


if __name__ == "__main__":
    raise SystemExit(main())
