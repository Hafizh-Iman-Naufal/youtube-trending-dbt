# Modeling Decisions

> Working notes captured during Phase 0. Each decision is grounded in the
> measurements in `docs/data-profile.md` and the manifest in
> `data/manifests/kaggle-youtube-new.json`.

## D1. Fact grain is `(region_code, video_id, trending_date)`

Confirmed by Phase 0 counts: every region has at most ~30k distinct video
IDs across ~200 trending dates. A video is observed many times.

**However** — 14,518 rows duplicate the grain key (concentrated in IN
4,894, JP 5,980, KR 2,625). These look like same-day re-pulls of the
trending list with the same metric snapshot. Phase 3 staging must dedup
deterministically (latest `_loaded_at`, or first-seen, picked in Phase 3).

## D2. `dim_video` grain is `(region_code, video_id)`, not `video_id`

The source has no global-region semantics. `category_id` is region-scoped.
If we joined a single `dim_video` on `video_id` alone, the same video
would inherit the wrong category when it trends in multiple regions.

## D3. No `dim_channel`

The source provides only `channel_title`. Same display name can refer to
different YouTube channels. We expose `channel_title` as a **reporting
dimension label** in `mart_channel_performance` only, not as a durable
foreign key.

## D4. Cumulative metrics are snapshots

`views`, `likes`, `dislikes`, `comment_count` are non-decreasing
cumulative counts in the source. Naive summation across days would
over-count. Marts use:

- **snapshot** measures (e.g. latest observation)
- **delta** measures (e.g. growth between observations)
- **count** measures (e.g. distinct trending appearances)

Never the literal `sum(views)` across observations.

## D5. `trending_date` parses as `YY.DD.MM` (not ISO)

Observed min/max across regions is `17.01.12` → `18.31.05`. The day slot
holding values up to 31 and month slot up to 12 confirms `YY.DD.MM`.
Two-digit-year rule: `00–69 → 20xx`, `70–99 → 19xx` (covers the snapshot).

## D6. Publish-after-trending is real and small

Phase 0 found ~19k rows (mostly MX/RU) where `publish_time > trending_date`.
This is expected for newly-published videos whose publication time happens
to land in a timezone-aware trending list. **Severity: warn**, not error.

## D7. Category `29` is region-specific

Every region's CSV uses `category_id = 29` at least once except US, yet
no region's category JSON contains `id = 29`. Treat as a known orphan;
the `(region_code, category_id)` join still works for everything else.

## D8. No snapshots

This is a static 2017–2018 historical extract, not a mutable source. dbt
`snapshots` would add ceremony without answering a real change-data
question. **Decision: no snapshots.**

## D9. No incremental materialization (yet)

Static dataset, ~375k rows, refresh is rare (only when re-downloaded).
A regular `table` materialization is reproducible and simpler. Phase 7
can revisit if the project ever moves to a live API feed.

## D10. Tags preserved raw in staging

Tag delimiter parsing is brittle; Phase 4 will add a conservative
`normalize_tags` macro that preserves raw and exposes only a
`tag_count` derived field unless Phase 4 profiling proves safe splitting.

## Open questions for later phases

- Phase 4: should `int_video_lifecycle` also expose day-over-day view delta?
- Phase 7: what is the right period grain for `mart_category_performance`
  — daily, weekly, or per-region-day?
- Phase 6: severity policy for `video_error_or_removed = true` — exclude
  from engagement metrics, or keep and flag?
