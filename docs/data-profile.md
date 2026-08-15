# Data Profile — Kaggle `datasnaek/youtube-new`

_Generated: 2026-08-15T14:46:51+00:00_

Source: <https://www.kaggle.com/datasets/datasnaek/youtube-new>  
License: CC0: Public Domain (per Kaggle page at acquisition time).

## Totals

- Total CSV rows: **375,942** across 10 regions
- Distinct video observations (region, video_id, trending_date): **361,424**
- Total duplicates of the grain key: **14,518**
- Total exact-duplicate rows: **12,570**
- Videos appearing in more than one region: **66,449**

## Per-CSV profile

| region | rows | distinct video_id | distinct trending_date | dup grain keys | exact dup rows | publish>trending | video_error_or_removed |
|---|---:|---:|---:|---:|---:|---:|---:|
| CA | 40,881 | 24,427 | 205 | 0 | 0 | 2,031 | 27 |
| DE | 40,840 | 29,627 | 205 | 0 | 0 | 836 | 14 |
| FR | 40,724 | 30,581 | 205 | 0 | 0 | 940 | 22 |
| GB | 38,916 | 3,272 | 205 | 174 | 171 | 56 | 69 |
| IN | 37,352 | 16,307 | 205 | 4,894 | 4,263 | 528 | 11 |
| JP | 20,523 | 12,912 | 122 | 5,980 | 5,677 | 1,840 | 12 |
| KR | 34,567 | 15,876 | 205 | 2,625 | 2,316 | 545 | 41 |
| MX | 40,451 | 33,513 | 205 | 378 | 49 | 9,608 | 24 |
| RU | 40,739 | 34,282 | 205 | 417 | 46 | 2,664 | 10 |
| US | 40,949 | 6,351 | 205 | 50 | 48 | 120 | 23 |

## Date range (parsed `YY.DD.MM`)

- **CA**: 17.01.12 → 18.31.05
- **DE**: 17.01.12 → 18.31.05
- **FR**: 17.01.12 → 18.31.05
- **GB**: 17.01.12 → 18.31.05
- **IN**: 17.01.12 → 18.31.05
- **JP**: 18.01.03 → 18.31.05
- **KR**: 17.01.12 → 18.31.05
- **MX**: 17.01.12 → 18.31.05
- **RU**: 17.01.12 → 18.31.05
- **US**: 17.01.12 → 18.31.05

## Null / blank counts per column (representative region: US)

| column | null count | null % |
|---|---:|---:|
| `description` | 570 | 1.39% |

## Type-parse failures

Counted across all regions. `0` means every non-null value parsed.

| column | failed parses |
|---|---:|
| _none_ | 0 |

## Numeric ranges

| measure | min | max | negative count |
|---|---:|---:|---:|
| `views` | 117 | 424538912 | 0 |
| `likes` | 0 | 5613827 | 0 |
| `dislikes` | 0 | 1944971 | 0 |
| `comment_count` | 0 | 1626501 | 0 |

## Boolean flag distributions (sums across regions)

| flag | True | False |
|---|---:|---:|
| `comments_disabled` | 8,463 | 367,479 |
| `ratings_disabled` | 7,308 | 368,634 |
| `video_error_or_removed` | 253 | 375,689 |

## Category reference integrity

| region | category IDs observed | without JSON match (total) | sample missing |
|---|---:|---:|---|
| CA | 17 | 1 | `CA:29` |
| DE | 18 | 1 | `DE:29` |
| FR | 18 | 1 | `FR:29` |
| GB | 16 | 1 | `GB:29` |
| IN | 17 | 1 | `IN:29` |
| JP | 15 | 1 | `JP:29` |
| KR | 17 | 1 | `KR:29` |
| MX | 16 | 1 | `MX:29` |
| RU | 17 | 1 | `RU:29` |
| US | 16 | 0 | `—` |

## Per-JSON profile

| region | items | dup ids | dup titles | null titles | assignable True |
|---|---:|---:|---:|---:|---:|
| CA | 31 | 0 | 1 | 0 | 14 |
| DE | 31 | 0 | 1 | 0 | 14 |
| FR | 31 | 0 | 1 | 0 | 14 |
| GB | 31 | 0 | 1 | 0 | 14 |
| IN | 31 | 0 | 1 | 0 | 14 |
| JP | 31 | 0 | 1 | 0 | 14 |
| KR | 31 | 0 | 1 | 0 | 14 |
| MX | 31 | 0 | 1 | 0 | 14 |
| RU | 31 | 0 | 1 | 0 | 14 |
| US | 32 | 0 | 1 | 0 | 15 |

## Cross-region overlap

- Videos appearing in 2+ regions: **66,449**
- Most-wide video: `#NAME?` appears in **2312** regions
- Videos with >1 distinct title (intra-region, US): **109** (title change events: 112)
- Videos with >1 distinct channel_title (intra-region, US): **12**

## Modeling decisions driven by this profile

- Grain `(region_code, video_id, trending_date)` is the **majority** key — but 14,518 duplicate-grain rows exist (concentrated in IN, JP, KR). These are likely same-day re-pulls of trending lists. Staging will keep one canonical row per grain key (e.g. latest snapshot); tests will pin the dedup policy.
- No `dim_channel` — `channel_title` is a display label, not a stable identifier.
- `dim_video` grain will be `(region_code, video_id)` since category IDs are region-scoped.
- Cumulative metrics (`views`/`likes`/`dislikes`/`comment_count`) are point-in-time snapshots — no naive summation.
- Two-digit year parsed as: 00–69 → 20xx, 70–99 → 19xx (covers the 2017–2018 snapshot window).
- Publish-after-trending violations are real (~19k rows total, mostly MX/RU) — likely UTC vs local-time edge cases; downgraded to a warning-severity test with documented tolerance.
- Category `29` exists in CSVs of every region except US but has no JSON title — likely a region-localised category. Join still requires `(region_code, category_id)`.

## Known limitations / open questions

- Profile is stdlib-only; deeper DuckDB-side checks happen in Phase 2 ingestion.
- `trending_date` two-digit year: assume 00–69 → 20xx, 70–99 → 19xx.
- Tags sampled only — full tag parsing deferred until Phase 4 macro design.
