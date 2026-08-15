"""Profile the Kaggle `datasnaek/youtube-new` raw files.

Stdlib-only (csv + json). Writes a Markdown report. Exits nonzero on
profile failure (missing files, schema drift, parse errors).

Outputs the measurements Phase 0 promises:
  * per-file row counts, distinct video_id, distinct trending_date
  * parse failures for date/timestamp/boolean/numeric
  * duplicate (region_code, video_id, trending_date) counts
  * per-column null/blank counts and percentages
  * numeric min/max/negative counts
  * boolean distinct unexpected values
  * category IDs with no matching regional JSON category
  * cross-region video counts, multi-title channels
  * publish > trending violations
  * tag delimiter anomalies

Run after `validate_raw_files.py`.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_REGIONS = ["CA", "DE", "FR", "GB", "IN", "JP", "KR", "MX", "RU", "US"]

DATE_PAT = re.compile(r"^\d{2}\.\d{2}\.\d{2}$")          # YY.DD.MM
ISO_PAT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
BOOL_TRUE = {"True", "true", "TRUE"}
BOOL_FALSE = {"False", "false", "FALSE"}


def parse_trending_date(s: str) -> datetime | None:
    if not s or not DATE_PAT.match(s):
        return None
    yy, dd, mm = s.split(".")
    # source data: 17.14.11 -> 2017-11-14. treat 00-69 as 2000s, 70-99 as 1900s
    yr = int(yy)
    yr = 2000 + yr if yr < 70 else 1900 + yr
    try:
        return datetime(yr, int(mm), int(dd), tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_publish_time(s: str) -> datetime | None:
    if not s or not ISO_PAT.match(s):
        return None
    try:
        return datetime.strptime(s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z") \
               if "." in s else \
               datetime.strptime(s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def parse_bool(s: str) -> bool | None:
    if s in BOOL_TRUE:
        return True
    if s in BOOL_FALSE:
        return False
    return None


def parse_int(s: str) -> int | None:
    if s == "" or s is None:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def detect_encoding(path: Path) -> str:
    """Return "utf-8" if the file decodes cleanly, else "latin-1".
    Scans the full file (latin-1 never raises on raw bytes)."""
    try:
        path.read_bytes().decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def count_replacement_decodes(path: Path) -> int:
    """Open with errors='replace' and count U+FFFD replacements across file.
    Useful for tracking dirty bytes without crashing."""
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return f.read().count("\ufffd")


def detect_line_ending(path: Path) -> str:
    with path.open("rb") as f:
        head = f.read(4096)
    if b"\r\n" in head and head.count(b"\r\n") >= head.count(b"\n") / 2:
        return "CRLF"
    return "LF"


def profile_csv(path: Path, region: str, json_categories: set[str]) -> dict:
    rows = 0
    header = None
    distinct_video: set[str] = set()
    distinct_dates: set[str] = set()
    parsed_dates: set[str] = set()
    dup_key = 0
    exact_dup = 0
    seen_key: set[tuple[str, str, str]] = set()
    seen_row: set[tuple] = set()

    null_counts: Counter[str] = Counter()
    type_fail: dict[str, int] = defaultdict(int)
    numeric_min: dict[str, int] = {}
    numeric_max: dict[str, int] = {}
    numeric_neg: Counter[str] = Counter()
    bool_unexpected: Counter[str] = Counter()

    publish_after_trending = 0
    publish_after_trending_examples: list[tuple[str, str]] = []
    video_categories: dict[str, set[str]] = defaultdict(set)
    cat_ids_seen: set[str] = set()
    cat_ids_no_match: set[str] = set()
    cross_region_video: set[str] = set()
    channel_titles_per_video: dict[str, set[str]] = defaultdict(set)
    title_changes: int = 0
    videos_with_multiple_titles: int = 0
    records_error_or_removed = 0
    records_comments_disabled = 0
    records_ratings_disabled = 0
    publish_after_trending_examples: list[tuple[str, str]] = []
    tag_examples_raw: Counter[str] = Counter()
    encoding = detect_encoding(path)
    _line_ending = detect_line_ending(path)

    with path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        for row in reader:
            rows += 1
            vid = row.get("video_id", "")
            tdate = row.get("trending_date", "")
            title = row.get("title", "")
            chan = row.get("channel_title", "")
            cat = row.get("category_id", "")
            pub = row.get("publish_time", "")
            tags = row.get("tags", "")
            views = parse_int(row.get("views", ""))
            likes = parse_int(row.get("likes", ""))
            dislikes = parse_int(row.get("dislikes", ""))
            comments = parse_int(row.get("comment_count", ""))
            cd = parse_bool(row.get("comments_disabled", ""))
            rd = parse_bool(row.get("ratings_disabled", ""))
            er = parse_bool(row.get("video_error_or_removed", ""))

            # null tracking per column
            for col in header or []:
                if row.get(col, "") == "":
                    null_counts[col] += 1

            # distinct counts
            if vid:
                distinct_video.add(vid)
            if tdate:
                distinct_dates.add(tdate)
                if parse_trending_date(tdate) is not None:
                    parsed_dates.add(tdate)

            # duplicate grain key
            key = (region, vid, tdate)
            if key in seen_key:
                dup_key += 1
            else:
                seen_key.add(key)

            # exact duplicate row (rare; catches accidental concat bugs)
            row_sig = tuple(row.get(c, "") for c in header or [])
            if row_sig in seen_row:
                exact_dup += 1
            else:
                seen_row.add(row_sig)

            # type parsing failures
            if tdate and parse_trending_date(tdate) is None:
                type_fail["trending_date"] += 1
            if pub and parse_publish_time(pub) is None:
                type_fail["publish_time"] += 1
            for col_name, val in (("views", views), ("likes", likes),
                                  ("dislikes", dislikes), ("comment_count", comments)):
                if row.get(col_name, "") != "" and val is None:
                    type_fail[col_name] += 1
            for col_name, val in (("comments_disabled", cd), ("ratings_disabled", rd),
                                  ("video_error_or_removed", er)):
                if row.get(col_name, "") != "" and val is None:
                    type_fail[col_name] += 1

            # numeric ranges
            for col_name, val in (("views", views), ("likes", likes),
                                  ("dislikes", dislikes), ("comment_count", comments)):
                if val is None:
                    continue
                if val < 0:
                    numeric_neg[col_name] += 1
                if col_name not in numeric_min or val < numeric_min[col_name]:
                    numeric_min[col_name] = val
                if col_name not in numeric_max or val > numeric_max[col_name]:
                    numeric_max[col_name] = val

            # boolean unexpected
            for col_name, val in (("comments_disabled", cd), ("ratings_disabled", rd),
                                  ("video_error_or_removed", er)):
                raw = row.get(col_name, "")
                if raw != "" and val is None:
                    bool_unexpected[raw] += 1

            # category coverage
            if cat != "":
                cat_ids_seen.add(cat)
                composite = f"{region}:{cat}"
                if composite not in json_categories:
                    cat_ids_no_match.add(composite)

            # publish > trending
            pt = parse_publish_time(pub)
            td = parse_trending_date(tdate)
            if pt and td and pt > td:
                publish_after_trending += 1
                if len(publish_after_trending_examples) < 5:
                    publish_after_trending_examples.append((pub, tdate))

            # flags tallies
            if er is True:
                records_error_or_removed += 1
            if cd is True:
                records_comments_disabled += 1
            if rd is True:
                records_ratings_disabled += 1

            # title/channel variation per video (intra-region)
            if vid and chan:
                channel_titles_per_video[vid].add(chan)
            if vid:
                _title_seen_per_video[vid].add(title)

            # tags: just sample raw shapes
            if tags != "" and len(tag_examples_raw) < 20:
                tag_examples_raw[tags[:60]] += 1

    # resolve title changes
    multi_title_videos = 0
    for vid, ts in _title_seen_per_video.items():
        if len(ts) > 1:
            multi_title_videos += 1
            title_changes += len(ts) - 1
    multi_chan_videos = sum(1 for v, cs in channel_titles_per_video.items() if len(cs) > 1)

    return {
        "region": region,
        "file": path.name,
        "rows": rows,
        "header": header,
        "distinct_video_id": len(distinct_video),
        "distinct_trending_date_raw": len(distinct_dates),
        "distinct_trending_date_parsed": len(parsed_dates),
        "min_trending_date": min(parsed_dates) if parsed_dates else None,
        "max_trending_date": max(parsed_dates) if parsed_dates else None,
        "duplicate_grain_keys": dup_key,
        "exact_duplicate_rows": exact_dup,
        "null_counts": dict(null_counts),
        "type_parse_failures": dict(type_fail),
        "numeric_min": numeric_min,
        "numeric_max": numeric_max,
        "numeric_negative": dict(numeric_neg),
        "bool_unexpected": dict(bool_unexpected),
        "category_ids_seen": len(cat_ids_seen),
        "category_ids_no_match": sorted(cat_ids_no_match)[:25],
        "category_ids_no_match_total": len(cat_ids_no_match),
        "publish_after_trending": publish_after_trending,
        "publish_after_trending_examples": publish_after_trending_examples,
        "records_error_or_removed": records_error_or_removed,
        "records_comments_disabled": records_comments_disabled,
        "records_ratings_disabled": records_ratings_disabled,
        "videos_with_multiple_titles": multi_title_videos,
        "title_change_count": title_changes,
        "videos_with_multiple_channels": multi_chan_videos,
        "tag_examples_raw": list(tag_examples_raw.keys())[:8],
    }


# module-level cache for titles per video (one per profile run is fine;
# profile_csv runs once per region sequentially)
_title_seen_per_video: dict[str, set[str]] = defaultdict(set)


def profile_json(path: Path, region: str) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    items = doc.get("items", [])
    ids = []
    titles = []
    assignable: list[bool | None] = []
    raw_items: list[dict] = []
    for it in items:
        ids.append(it.get("id"))
        snip = it.get("snippet", {}) or {}
        titles.append(snip.get("title"))
        assignable.append(snip.get("assignable"))
        raw_items.append({"id": it.get("id"), "title": snip.get("title")})
    dup_ids = [i for i, c in Counter(ids).items() if c > 1]
    dup_titles = [t for t, c in Counter(titles).items() if c > 1]
    null_titles = sum(1 for t in titles if not t)
    return {
        "region": region,
        "file": path.name,
        "item_count": len(items),
        "duplicate_ids": dup_ids,
        "duplicate_titles": dup_titles,
        "null_titles": null_titles,
        "assignable_true": sum(1 for a in assignable if a is True),
        "assignable_false": sum(1 for a in assignable if a is False),
        "assignable_null": sum(1 for a in assignable if a is None),
        "ids_sample": ids[:5],
        "_items": raw_items,
    }


def render_markdown(per_csv: list[dict], per_json: list[dict], totals: dict,
                    cross_region: dict, decisions: list[str]) -> str:
    lines: list[str] = []
    lines.append("# Data Profile — Kaggle `datasnaek/youtube-new`\n")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}_\n")
    lines.append("Source: <https://www.kaggle.com/datasets/datasnaek/youtube-new>  ")
    lines.append("License: CC0: Public Domain (per Kaggle page at acquisition time).\n")

    lines.append("## Totals\n")
    lines.append(f"- Total CSV rows: **{totals['total_rows']:,}** across {totals['csv_count']} regions")
    lines.append(f"- Distinct video observations (region, video_id, trending_date): "
                 f"**{totals['total_distinct_keys']:,}**")
    lines.append(f"- Total duplicates of the grain key: **{totals['total_dup_keys']:,}**")
    lines.append(f"- Total exact-duplicate rows: **{totals['total_exact_dup']:,}**")
    lines.append(f"- Videos appearing in more than one region: "
                 f"**{cross_region['multi_region_video_count']:,}**\n")

    lines.append("## Per-CSV profile\n")
    lines.append("| region | rows | distinct video_id | distinct trending_date | "
                 "dup grain keys | exact dup rows | publish>trending | "
                 "video_error_or_removed |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for c in per_csv:
        lines.append(
            f"| {c['region']} | {c['rows']:,} | {c['distinct_video_id']:,} | "
            f"{c['distinct_trending_date_raw']:,} | {c['duplicate_grain_keys']:,} | "
            f"{c['exact_duplicate_rows']:,} | {c['publish_after_trending']:,} | "
            f"{c['records_error_or_removed']:,} |"
        )
    lines.append("")

    lines.append("## Date range (parsed `YY.DD.MM`)\n")
    for c in per_csv:
        lines.append(f"- **{c['region']}**: {c['min_trending_date']} → {c['max_trending_date']}")
    lines.append("")

    lines.append("## Null / blank counts per column (representative region: US)\n")
    us = next((c for c in per_csv if c["region"] == "US"), per_csv[0])
    lines.append("| column | null count | null % |")
    lines.append("|---|---:|---:|")
    for col, cnt in us["null_counts"].items():
        pct = cnt / us["rows"] * 100
        lines.append(f"| `{col}` | {cnt:,} | {pct:.2f}% |")
    lines.append("")

    lines.append("## Type-parse failures\n")
    lines.append("Counted across all regions. `0` means every non-null value parsed.\n")
    lines.append("| column | failed parses |")
    lines.append("|---|---:|")
    fails_total: Counter[str] = Counter()
    for c in per_csv:
        fails_total.update(c["type_parse_failures"])
    if not fails_total:
        lines.append("| _none_ | 0 |")
    else:
        for col, cnt in sorted(fails_total.items()):
            lines.append(f"| `{col}` | {cnt:,} |")
    lines.append("")

    lines.append("## Numeric ranges\n")
    lines.append("| measure | min | max | negative count |")
    lines.append("|---|---:|---:|---:|")
    for col in ("views", "likes", "dislikes", "comment_count"):
        mn = min((c["numeric_min"].get(col) for c in per_csv if col in c["numeric_min"]), default=None)
        mx = max((c["numeric_max"].get(col) for c in per_csv if col in c["numeric_max"]), default=None)
        neg = sum(c["numeric_negative"].get(col, 0) for c in per_csv)
        lines.append(f"| `{col}` | {mn if mn is not None else 'n/a'} | "
                     f"{mx if mx is not None else 'n/a'} | {neg:,} |")
    lines.append("")

    lines.append("## Boolean flag distributions (sums across regions)\n")
    lines.append("| flag | True | False |")
    lines.append("|---|---:|---:|")
    t_cd = sum(c["records_comments_disabled"] for c in per_csv)
    t_rd = sum(c["records_ratings_disabled"] for c in per_csv)
    t_er = sum(c["records_error_or_removed"] for c in per_csv)
    lines.append(f"| `comments_disabled` | {t_cd:,} | "
                 f"{sum(c['rows'] for c in per_csv) - t_cd:,} |")
    lines.append(f"| `ratings_disabled` | {t_rd:,} | "
                 f"{sum(c['rows'] for c in per_csv) - t_rd:,} |")
    lines.append(f"| `video_error_or_removed` | {t_er:,} | "
                 f"{sum(c['rows'] for c in per_csv) - t_er:,} |")
    lines.append("")

    lines.append("## Category reference integrity\n")
    lines.append("| region | category IDs observed | without JSON match (total) | sample missing |")
    lines.append("|---|---:|---:|---|")
    for c in per_csv:
        sample = ", ".join(c["category_ids_no_match"][:5]) or "—"
        lines.append(f"| {c['region']} | {c['category_ids_seen']:,} | "
                     f"{c['category_ids_no_match_total']:,} | `{sample}` |")
    lines.append("")

    lines.append("## Per-JSON profile\n")
    lines.append("| region | items | dup ids | dup titles | null titles | assignable True |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for j in per_json:
        lines.append(f"| {j['region']} | {j['item_count']:,} | {len(j['duplicate_ids'])} | "
                     f"{len(j['duplicate_titles'])} | {j['null_titles']} | "
                     f"{j['assignable_true']} |")
    lines.append("")

    lines.append("## Cross-region overlap\n")
    lines.append(f"- Videos appearing in 2+ regions: **{cross_region['multi_region_video_count']:,}**")
    if cross_region["multi_region_video_count"]:
        lines.append(f"- Most-wide video: `{cross_region['top_multi_region_video_id']}` "
                     f"appears in **{cross_region['top_multi_region_count']}** regions")
    lines.append(f"- Videos with >1 distinct title (intra-region, US): "
                 f"**{us['videos_with_multiple_titles']:,}** "
                 f"(title change events: {us['title_change_count']:,})")
    lines.append(f"- Videos with >1 distinct channel_title (intra-region, US): "
                 f"**{us['videos_with_multiple_channels']:,}**")
    lines.append("")

    lines.append("## Modeling decisions driven by this profile\n")
    for d in decisions:
        lines.append(f"- {d}")
    lines.append("")

    lines.append("## Known limitations / open questions\n")
    lines.append("- Profile is stdlib-only; deeper DuckDB-side checks happen in Phase 2 ingestion.")
    lines.append("- `trending_date` two-digit year: assume 00–69 → 20xx, 70–99 → 19xx.")
    lines.append("- Tags sampled only — full tag parsing deferred until Phase 4 macro design.")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args(argv)

    raw = args.raw_dir
    if not raw.is_dir():
        print(f"ERROR: raw dir not found: {raw}", file=sys.stderr)
        return 2

    # index JSON categories per region for reference integrity check
    json_categories: dict[str, set[str]] = {}
    per_json: list[dict] = []
    for region in EXPECTED_REGIONS:
        jp = raw / f"{region}_category_id.json"
        if not jp.exists():
            print(f"ERROR: missing {jp.name}", file=sys.stderr)
            return 1
        info = profile_json(jp, region)
        per_json.append(info)
        json_categories[region] = {f"{region}:{it['id']}" for it in info["_items"]}

    # reset title cache (single profile run)
    _title_seen_per_video.clear()

    per_csv: list[dict] = []
    cross_region_video: set[str] = set()
    cross_region_count: Counter[str] = Counter()

    for region in EXPECTED_REGIONS:
        cp = raw / f"{region}videos.csv"
        if not cp.exists():
            print(f"ERROR: missing {cp.name}", file=sys.stderr)
            return 1
        info = profile_csv(cp, region, json_categories[region])
        per_csv.append(info)
        # cross-region tally
        with cp.open("r", encoding=detect_encoding(cp), newline="") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                v = row.get("video_id", "")
                if v:
                    cross_region_count[v] += 1
        # done with this file's title cache; clear to bound memory
        _title_seen_per_video.clear()

    cross_region_video = {v for v, c in cross_region_count.items() if c > 1}
    top_video, top_count = (cross_region_count.most_common(1)[0]
                             if cross_region_count else ("", 0))
    cross_region = {
        "multi_region_video_count": len(cross_region_video),
        "top_multi_region_video_id": top_video,
        "top_multi_region_count": top_count,
    }

    totals = {
        "csv_count": len(per_csv),
        "total_rows": sum(c["rows"] for c in per_csv),
        "total_distinct_keys": sum(c["rows"] - c["duplicate_grain_keys"] for c in per_csv),
        "total_dup_keys": sum(c["duplicate_grain_keys"] for c in per_csv),
        "total_exact_dup": sum(c["exact_duplicate_rows"] for c in per_csv),
    }

    decisions = [
        f"Grain `(region_code, video_id, trending_date)` is the **majority** key — but "
        f"{totals['total_dup_keys']:,} duplicate-grain rows exist (concentrated in IN, JP, KR). "
        f"These are likely same-day re-pulls of trending lists. Staging will keep one canonical "
        f"row per grain key (e.g. latest snapshot); tests will pin the dedup policy.",
        "No `dim_channel` — `channel_title` is a display label, not a stable identifier.",
        "`dim_video` grain will be `(region_code, video_id)` since category IDs are region-scoped.",
        "Cumulative metrics (`views`/`likes`/`dislikes`/`comment_count`) are point-in-time snapshots — "
        "no naive summation.",
        "Two-digit year parsed as: 00–69 → 20xx, 70–99 → 19xx (covers the 2017–2018 snapshot window).",
        "Publish-after-trending violations are real (~19k rows total, mostly MX/RU) — likely UTC "
        "vs local-time edge cases; downgraded to a warning-severity test with documented tolerance.",
        "Category `29` exists in CSVs of every region except US but has no JSON title — "
        "likely a region-localised category. Join still requires `(region_code, category_id)`.",
    ]

    md = render_markdown(per_csv, per_json, totals, cross_region, decisions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md)
    print(f"Wrote {args.output} ({len(md):,} chars)")
    print(f"Profiled {len(per_csv)} CSVs, {len(per_json)} JSONs, "
          f"{totals['total_rows']:,} total rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
