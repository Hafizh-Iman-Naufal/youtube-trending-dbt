# Metric Definitions

Every metric in this project states its **type** explicitly. Cumulative
source measures (`views`, `likes`, `dislikes`, `comment_count`) are
**point-in-time snapshots**, NOT deltas. Never sum them across dates.

## Snapshot measures (do NOT sum across observations)

| Metric | Source column | Definition |
|---|---|---|
| `views` | `views` | Cumulative views at the trending observation date |
| `likes` | `likes` | Cumulative likes at the observation date |
| `dislikes` | `dislikes` | Cumulative dislikes at the observation date |
| `comment_count` | `comment_count` | Cumulative comments at the observation date |

## Derived rates (NULL when denominator is invalid)

| Metric | Definition | NULL when |
|---|---|---|
| `like_rate` | `likes / views` | `views` = 0 or NULL |
| `dislike_rate` | `dislikes / views` | `views` = 0 or NULL |
| `comment_rate` | `comment_count / views` | `views` = 0 or NULL |
| `engagement_rate` | `(likes + dislikes + comment_count) / views` | `views` = 0 or NULL |

Computed via the `safe_divide` macro.

## Validity flag

`has_valid_engagement` (BOOLEAN) is `false` when:

- `video_error_or_removed = true` (data invalid)
- `ratings_disabled = true` (likes/dislikes may be inaccurate)
- `views` is 0 or NULL (denominator undefined)

Downstream marts MUST filter on `has_valid_engagement = true` before
computing engagement averages, or rates will be misleading.

## Lifecycle metrics (per `region_code, video_id`)

| Metric | Definition |
|---|---|
| `first_trending_date` | Earliest trending appearance date |
| `last_trending_date` | Latest trending appearance date |
| `observed_trending_days` | `COUNT(DISTINCT trending_date_parsed)` |
| `latest_views` | `views` at the latest observation (snapshot) |
| `peak_views` | `MAX(views)` across all observations |
| `days_publish_to_first_trending` | `first_trending_date - publish_time::DATE` |
| `days_since_publish` | `trending_date - publish_time::DATE` (per observation) |

## Counts (events)

| Metric | Definition |
|---|---|
| `tag_count` | Number of pipe-delimited tags after normalization |

## NOT computed (deliberately)

- `total_views` / `total_engagement` — would naively sum cumulative
  snapshots and double-count. Use `peak_views` or `latest_views` instead.
- "Viral" / "trending velocity" — would require a defined causal
  model not supported by the source.
- Per-user retention — no user-level data in this dataset.
