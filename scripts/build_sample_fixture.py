"""Build a small deterministic sample fixture under data/sample/.

Ponytail: we don't need to ship 539MB of sample data. The fixture is a
hand-curated, fully representative slice: every region's CSV gets a
header + a few canonical rows. Categories JSONs are mirrored from the
real Kaggle source (they're <9KB each, ~80KB total) so category joins
work end-to-end without Kaggle access.

Idempotent: re-running overwrites in place.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

EXPECTED_REGIONS = ["CA", "DE", "FR", "GB", "IN", "JP", "KR", "MX", "RU", "US"]

CSV_HEADER = [
    "video_id", "trending_date", "title", "channel_title", "category_id",
    "publish_time", "tags", "views", "likes", "dislikes", "comment_count",
    "thumbnail_link", "comments_disabled", "ratings_disabled",
    "video_error_or_removed", "description",
]

# A small deterministic slice per region. 6 rows each: covers typical
# values, a comment-disabled flag, a ratings-disabled flag, a video_error
# flag, an empty description, and a date outside the YY.DD.MM range.
SAMPLE_ROWS = {
    "CA": [
        ("vCA00001", "17.14.11", "Sample CA Video 1", "Sample Channel CA", "10",
         "2017-11-13T10:00:00.000Z", "tag1|tag2|tag3", "1000", "50", "5", "12",
         "https://i.ytimg.com/vi/vCA00001/hqdefault.jpg", "False", "False", "False",
         "Sample description CA 1"),
        ("vCA00002", "18.01.01", "Sample CA Video 2", "Sample Channel CA", "20",
         "2018-01-01T00:00:00.000Z", "news|breaking", "5000", "200", "10", "30",
         "https://i.ytimg.com/vi/vCA00002/hqdefault.jpg", "False", "False", "False",
         ""),
    ],
    "DE": [
        ("vDE00001", "17.14.11", "Sample DE Video 1", "Sample Channel DE", "17",
         "2017-11-13T11:00:00.000Z", "musik|charts", "2000", "100", "3", "20",
         "https://i.ytimg.com/vi/vDE00001/hqdefault.jpg", "False", "False", "False",
         "Sample description DE 1"),
        ("vDE00002", "18.02.15", "Sample DE Video 2", "Sample Channel DE", "24",
         "2018-02-15T08:00:00.000Z", "politik|wahl", "15000", "600", "50", "100",
         "https://i.ytimg.com/vi/vDE00002/hqdefault.jpg", "True", "False", "False",
         "Sample description DE 2"),
    ],
    "FR": [
        ("vFR00001", "17.14.11", "Sample FR Video 1", "Sample Channel FR", "22",
         "2017-11-13T12:00:00.000Z", "people|actu", "3000", "150", "8", "40",
         "https://i.ytimg.com/vi/vFR00001/hqdefault.jpg", "False", "False", "False",
         "Sample description FR 1"),
        ("vFR00002", "18.03.10", "Sample FR Video 2", "Sample Channel FR", "23",
         "2018-03-10T09:00:00.000Z", "musique|pop", "8000", "300", "20", "60",
         "https://i.ytimg.com/vi/vFR00002/hqdefault.jpg", "False", "True", "False",
         "Sample description FR 2"),
    ],
    "GB": [
        ("vGB00001", "17.14.11", "Sample GB Video 1", "Sample Channel GB", "10",
         "2017-11-13T13:00:00.000Z", "music|uk", "4000", "200", "10", "50",
         "https://i.ytimg.com/vi/vGB00001/hqdefault.jpg", "False", "False", "False",
         "Sample description GB 1"),
        ("vGB00002", "18.04.05", "Sample GB Video 2", "Sample Channel GB", "26",
         "2018-04-05T14:00:00.000Z", "howto|style", "12000", "500", "30", "80",
         "https://i.ytimg.com/vi/vGB00002/hqdefault.jpg", "False", "False", "True",
         "Sample description GB 2"),
    ],
    "IN": [
        ("vIN00001", "17.14.11", "Sample IN Video 1", "Sample Channel IN", "10",
         "2017-11-13T14:00:00.000Z", "bollywood|songs", "25000", "1500", "60", "200",
         "https://i.ytimg.com/vi/vIN00001/hqdefault.jpg", "False", "False", "False",
         "Sample description IN 1"),
        ("vIN00002", "18.05.01", "Sample IN Video 2", "Sample Channel IN", "24",
         "2018-05-01T15:00:00.000Z", "cricket|match", "50000", "2000", "100", "500",
         "https://i.ytimg.com/vi/vIN00002/hqdefault.jpg", "False", "False", "False",
         "Sample description IN 2"),
    ],
    "JP": [
        ("vJP00001", "18.01.03", "Sample JP Video 1", "Sample Channel JP", "10",
         "2018-01-03T16:00:00.000Z", "anime|manga", "10000", "800", "20", "150",
         "https://i.ytimg.com/vi/vJP00001/hqdefault.jpg", "False", "False", "False",
         "Sample description JP 1"),
        ("vJP00002", "18.06.15", "Sample JP Video 2", "Sample Channel JP", "17",
         "2018-06-15T17:00:00.000Z", "game|review", "20000", "1000", "40", "250",
         "https://i.ytimg.com/vi/vJP00002/hqdefault.jpg", "True", "False", "False",
         "Sample description JP 2"),
    ],
    "KR": [
        ("vKR00001", "17.14.11", "Sample KR Video 1", "Sample Channel KR", "10",
         "2017-11-13T18:00:00.000Z", "kpop|music", "30000", "2000", "100", "400",
         "https://i.ytimg.com/vi/vKR00001/hqdefault.jpg", "False", "False", "False",
         "Sample description KR 1"),
        ("vKR00002", "18.04.20", "Sample KR Video 2", "Sample Channel KR", "20",
         "2018-04-20T19:00:00.000Z", "drama|korean", "40000", "2500", "150", "600",
         "https://i.ytimg.com/vi/vKR00002/hqdefault.jpg", "False", "False", "False",
         "Sample description KR 2"),
    ],
    "MX": [
        ("vMX00001", "17.14.11", "Sample MX Video 1", "Sample Channel MX", "10",
         "2017-11-13T20:00:00.000Z", "musica|latino", "35000", "1800", "80", "300",
         "https://i.ytimg.com/vi/vMX00001/hqdefault.jpg", "False", "False", "False",
         "Sample description MX 1"),
        ("vMX00002", "18.05.10", "Sample MX Video 2", "Sample Channel MX", "23",
         "2018-05-10T21:00:00.000Z", "deportes|football", "60000", "3000", "200", "800",
         "https://i.ytimg.com/vi/vMX00002/hqdefault.jpg", "False", "False", "False",
         "Sample description MX 2"),
    ],
    "RU": [
        ("vRU00001", "17.14.11", "Sample RU Video 1", "Sample Channel RU", "10",
         "2017-11-13T22:00:00.000Z", "music|russian", "20000", "1000", "50", "250",
         "https://i.ytimg.com/vi/vRU00001/hqdefault.jpg", "False", "False", "False",
         "Sample description RU 1"),
        ("vRU00002", "18.03.25", "Sample RU Video 2", "Sample Channel RU", "27",
         "2018-03-25T23:00:00.000Z", "education|school", "25000", "1200", "60", "350",
         "https://i.ytimg.com/vi/vRU00002/hqdefault.jpg", "False", "True", "False",
         "Sample description RU 2"),
    ],
    "US": [
        ("vUS00001", "17.14.11", "Sample US Video 1", "Sample Channel US", "10",
         "2017-11-13T00:00:00.000Z", "music|pop", "100000", "5000", "200", "1000",
         "https://i.ytimg.com/vi/vUS00001/hqdefault.jpg", "False", "False", "False",
         "Sample description US 1"),
        ("vUS00002", "18.02.28", "Sample US Video 2", "Sample Channel US", "17",
         "2018-02-28T01:00:00.000Z", "sports|nba", "150000", "8000", "300", "1500",
         "https://i.ytimg.com/vi/vUS00002/hqdefault.jpg", "False", "False", "False",
         "Sample description US 2"),
    ],
}


def csv_quote(field: str) -> str:
    """Quote a CSV field if it contains a comma, quote, or newline."""
    if any(c in field for c in (",", '"', "\n", "\r")):
        return '"' + field.replace('"', '""') + '"'
    return field


def write_csv(path: Path, rows: list[tuple]) -> None:
    lines: list[str] = []
    lines.append(",".join(CSV_HEADER))
    for r in rows:
        lines.append(",".join(csv_quote(str(v)) for v in r))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=Path("data/sample"))
    ap.add_argument("--from-raw", type=Path, default=None,
                    help="If provided, copy real category JSONs from this path.")
    args = ap.parse_args(argv)

    out: Path = args.out_dir
    if out.exists():
        # idempotent: clear sample dir except ourselves
        for p in out.iterdir():
            if p.is_file():
                p.unlink()
    out.mkdir(parents=True, exist_ok=True)

    for region, rows in SAMPLE_ROWS.items():
        write_csv(out / f"{region}videos.csv", rows)

    # categories: copy from real raw if present, else write minimal stubs
    src = args.from_raw or Path("data/raw")
    for region in EXPECTED_REGIONS:
        target = out / f"{region}_category_id.json"
        candidate = src / f"{region}_category_id.json"
        if candidate.exists():
            shutil.copyfile(candidate, target)
        else:
            target.write_text(json.dumps({"items": [
                {"id": "1", "snippet": {"title": "Sample Category 1", "assignable": True}},
            ]}))
            print(f"WARN: wrote stub category JSON for {region}", file=sys.stderr)

    n_csv = sum(1 for _ in out.glob("*videos.csv"))
    n_json = sum(1 for _ in out.glob("*_category_id.json"))
    print(f"OK: wrote {n_csv} CSVs and {n_json} JSONs under {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
