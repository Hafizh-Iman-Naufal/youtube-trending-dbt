"""Validate structural integrity of Kaggle `datasnaek/youtube-new` raw files.

Stdlib-only so Phase 0 runs without installing DuckDB or dbt. Use this
script before any ingestion. Exits nonzero on missing, extra, malformed,
or schema-drifted files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

EXPECTED_REGIONS = ["CA", "DE", "FR", "GB", "IN", "JP", "KR", "MX", "RU", "US"]

# 16 columns observed in every regional CSV (header order matters).
EXPECTED_CSV_HEADER = [
    "video_id",
    "trending_date",
    "title",
    "channel_title",
    "category_id",
    "publish_time",
    "tags",
    "views",
    "likes",
    "dislikes",
    "comment_count",
    "thumbnail_link",
    "comments_disabled",
    "ratings_disabled",
    "video_error_or_removed",
    "description",
]

# JSON category item fields we expect to find at least.
EXPECTED_JSON_ITEM_KEYS = {"id", "snippet"}


class ValidationError(Exception):
    pass


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda: f.read(chunk), b""):
            h.update(buf)
    return h.hexdigest()


def detect_line_ending(path: Path) -> str:
    with path.open("rb") as f:
        head = f.read(4096)
    if b"\r\n" in head and head.count(b"\r\n") >= head.count(b"\n") / 2:
        return "CRLF"
    return "LF"


def detect_encoding(path: Path) -> str:
    # cheap heuristic: try utf-8 first; fall back to latin-1 if it fails
    data = path.read_bytes()[:8192]
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def validate_csv(path: Path) -> dict:
    info: dict = {"file": path.name, "type": "csv"}
    info["size_bytes"] = path.stat().st_size
    info["sha256"] = sha256_file(path)
    info["encoding"] = detect_encoding(path)
    info["line_ending"] = detect_line_ending(path)

    # csv.Sniffer is unreliable on these files; use first line literally.
    with path.open("r", encoding=info["encoding"], newline="") as f:
        first = f.readline()
        # csv.reader handles quoted commas inside the header itself, but
        # the header here is simple — strip newline + split.
        raw_header = first.rstrip("\r\n")
        header = next(csv.reader(io.StringIO(raw_header)))

    if header != EXPECTED_CSV_HEADER:
        raise ValidationError(
            f"{path.name}: header drift.\n"
            f"  expected: {EXPECTED_CSV_HEADER}\n"
            f"  got     : {header}"
        )
    info["header"] = header
    info["column_count"] = len(header)
    return info


def validate_json(path: Path) -> dict:
    info: dict = {"file": path.name, "type": "json"}
    info["size_bytes"] = path.stat().st_size
    info["sha256"] = sha256_file(path)
    info["encoding"] = detect_encoding(path)

    with path.open("r", encoding=info["encoding"]) as f:
        doc = json.load(f)

    if not isinstance(doc, dict) or "items" not in doc or not isinstance(doc["items"], list):
        raise ValidationError(f"{path.name}: missing top-level 'items' array")

    items = doc["items"]
    info["item_count"] = len(items)
    info["items"] = []  # compact per-item summary

    for it in items:
        if not isinstance(it, dict):
            raise ValidationError(f"{path.name}: non-object item in items")
        missing = EXPECTED_JSON_ITEM_KEYS - set(it.keys())
        if missing:
            raise ValidationError(f"{path.name}: item missing keys {sorted(missing)}")
        snip = it.get("snippet", {})
        title = snip.get("title") if isinstance(snip, dict) else None
        info["items"].append(
            {
                "id": it.get("id"),
                "title": title,
                "assignable": snip.get("assignable") if isinstance(snip, dict) else None,
            }
        )
    return info


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", required=True, type=Path)
    ap.add_argument("--json-out", type=Path, default=None,
                    help="Optional: write a structured report as JSON")
    ap.add_argument("--strict", action="store_true",
                    help="Treat warnings (extra files) as failures")
    args = ap.parse_args(argv)

    raw: Path = args.raw_dir
    if not raw.is_dir():
        print(f"ERROR: raw dir not found: {raw}", file=sys.stderr)
        return 2

    found_csv = sorted(p.name for p in raw.glob("*videos.csv"))
    found_json = sorted(p.name for p in raw.glob("*_category_id.json"))

    expected_csv = sorted(f"{r}videos.csv" for r in EXPECTED_REGIONS)
    expected_json = sorted(f"{r}_category_id.json" for r in EXPECTED_REGIONS)

    extras_csv = sorted(set(found_csv) - set(expected_csv))
    extras_json = sorted(set(found_json) - set(expected_json))
    missing_csv = sorted(set(expected_csv) - set(found_csv))
    missing_json = sorted(set(expected_json) - set(found_json))

    report: dict = {
        "raw_dir": str(raw.resolve()),
        "expected_regions": EXPECTED_REGIONS,
        "csv": {"found": found_csv, "missing": missing_csv, "extra": extras_csv},
        "json": {"found": found_json, "missing": missing_json, "extra": extras_json},
        "files": [],
    }

    if missing_csv or missing_json:
        print(f"FAIL: missing files. csv missing={missing_csv} json missing={missing_json}",
              file=sys.stderr)
        return 1
    if (extras_csv or extras_json) and args.strict:
        print(f"FAIL: unexpected extra files. csv={extras_csv} json={extras_json}",
              file=sys.stderr)
        return 1
    if extras_csv or extras_json:
        print(f"WARN: unexpected extra files (ignored, --strict to fail). "
              f"csv={extras_csv} json={extras_json}", file=sys.stderr)

    failed = 0
    for name in expected_csv:
        try:
            report["files"].append(validate_csv(raw / name))
        except ValidationError as e:
            print(f"FAIL: {e}", file=sys.stderr)
            failed += 1

    for name in expected_json:
        try:
            report["files"].append(validate_json(raw / name))
        except ValidationError as e:
            print(f"FAIL: {e}", file=sys.stderr)
            failed += 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True))

    if failed:
        print(f"\n{failed} file(s) failed validation.", file=sys.stderr)
        return 1

    csv_total = sum(f["size_bytes"] for f in report["files"] if f["type"] == "csv")
    json_total = sum(f["size_bytes"] for f in report["files"] if f["type"] == "json")
    print(f"OK: {len(found_csv)} CSVs ({csv_total:,} bytes), "
          f"{len(found_json)} JSONs ({json_total:,} bytes). "
          f"All 20 expected files present with correct schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
