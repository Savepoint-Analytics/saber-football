# NFL Public Data Sources and Access Patterns

Last updated: 2026-07-08

## Summary

NFL public analytics data is strongest at the play-by-play level. The best public ecosystem is `nflverse`, especially `nflfastR`, `nflreadr`, `nfl_data_py`, and `nflreadpy`. Most NFL public data is not a traditional query API. It is usually exposed as package loaders and downloadable release files, commonly CSV, Parquet, RDS, or QS. For a serious analytics project, treat these as source extracts that should be stored locally in your own warehouse.

## Storage vs API expectation

| Source family | Access style | Should you store it? | Reason |
|---|---:|---:|---|
| nflverse / nflfastR / nflreadr | Package loaders over public release files | Yes | Public releases are easy to reload, but versioned local snapshots protect reproducibility. |
| nfl_data_py / nflreadpy | Python package loaders over nflverse data | Yes | Python-first access is convenient, but model rebuilds should not depend on mutable remote state. |
| NFL Next Gen Stats public pages | Public web pages / aggregated stats, often accessed through nflverse mirrors | Yes | Public site data can change and raw tracking is not fully public. |
| NFL Big Data Bowl | Kaggle competition download | Yes | Data is a static research artifact; must be downloaded and stored. |
| Pro Football Reference / Sports Reference | Web tables / Stathead paid querying | Yes, if used | Scraping and terms/rate limits require caution; store derived extracts and document provenance. |
| NFLPA salary cap report | Web report | Yes | Daily-changing cap state should be snapshotted by date. |
| OverTheCap / Spotrac | Web data; some package mirrors; paid tools possible | Yes | Contract data changes with restructures, cuts, void years, and cap accounting updates. |
| Betting lines / market data | Available partly through nflverse schedules and other sources | Yes | Closing lines and timestamps matter. Store source and line timing. |
| Weather/stadium | Schedules, public weather, stadium metadata | Yes | Weather can be source-dependent; game-time weather should be snapshotted. |

## Core NFL data sources

### 1. nflverse

- URL: https://nflverse.nflverse.com/
- GitHub data releases: https://github.com/nflverse/nflverse-data/releases
- What it is: a collection of packages and data repositories for NFL analytics.
- Why it matters: it is the default open-source data backbone for NFL analytics.
- Access: R packages, Python packages, and public release files.
- Storage recommendation: store a local copy of every table used in modeling, partitioned by season and source version.

The nflverse GitHub organization notes that most data is stored in releases of the `nflverse-data` repository in formats such as CSV, Parquet, RDS, and QS, which can be accessed by any platform through web URLs.

### 2. nflfastR

- URL: https://nflfastr.com/
- What it gives you: NFL play-by-play data, expected points, win probability, completion probability, CPOE, and YAC-related modeled fields.
- Historical depth: nflfastR hosts play-by-play data going back to 1999.
- Access:

```r
library(nflfastR)
library(nflreadr)

schedules <- load_schedules(1999:2025)
pbp <- load_pbp(1999:2025)
```

Python-first option:

```python
import nfl_data_py as nfl

pbp = nfl.import_pbp_data(range(1999, 2026))
schedules = nfl.import_schedules(range(1999, 2026))
```

Storage recommendation: store play-by-play as Parquet partitioned by `season`, `season_type`, and optionally `week`. Play-by-play is the central fact table for all downstream modeling.

### 3. nflreadr

- URL: https://nflreadr.nflverse.com/
- What it gives you: package loaders and dictionaries for schedules, rosters, player stats, contracts, injuries, snap counts, depth charts, participation, combine, draft, ESPN QBR, team stats, trades, and more.
- Important documentation: https://nflreadr.nflverse.com/reference/index.html

Useful R access examples:

```r
library(nflreadr)

pbp <- load_pbp(2020:2025)
weekly <- load_player_stats(2020:2025)
rosters <- load_rosters(2020:2025)
schedules <- load_schedules(2020:2025)
contracts <- load_contracts()
snap_counts <- load_snap_counts(2020:2025)
injuries <- load_injuries(2020:2025)
combine <- load_combine()
draft <- load_draft_picks()
participation <- load_participation(2016:2025)
ngs_passing <- load_nextgen_stats(2016:2025, stat_type = "passing")
ngs_receiving <- load_nextgen_stats(2016:2025, stat_type = "receiving")
ngs_rushing <- load_nextgen_stats(2016:2025, stat_type = "rushing")
```

Storage recommendation: store every nflreadr table you rely on. The loader makes access easy, but local storage gives you reproducibility, faster joining, and a stable model input layer.

### 4. nfl_data_py

- URL: https://github.com/nflverse/nfl_data_py
- What it gives you: Python access to play-by-play, weekly data, seasonal data, rosters, win totals, scoring lines, officials, draft picks, draft pick values, schedules, team info, combine results, and player ID mappings.
- Best use: Python-first ingestion or notebooks.

Example:

```python
import nfl_data_py as nfl

seasons = range(2016, 2026)
pbp = nfl.import_pbp_data(seasons)
weekly = nfl.import_weekly_data(seasons)
rosters = nfl.import_seasonal_rosters(seasons)
combine = nfl.import_combine_data()
schedules = nfl.import_schedules(seasons)
ids = nfl.import_ids()
```

Storage recommendation: store in DuckDB, Postgres, or Parquet after ingestion.

### 5. nflreadpy

- URL: https://github.com/nflverse/nflreadpy
- What it gives you: a Python port of `nflreadr`, using Polars-style workflows.
- Best use: Python projects that want a loader interface closer to `nflreadr`.

Example:

```python
import nflreadpy as nfl

pbp = nfl.load_pbp([2024, 2025])
player_stats = nfl.load_player_stats([2024, 2025])
team_stats = nfl.load_team_stats(seasons=True)
```

### 6. NFL Next Gen Stats

- URL: https://nextgenstats.nfl.com/
- What it gives you: public aggregate NGS metrics for passing, rushing, receiving, and other player measures.
- Important caution: the NFL says Next Gen Stats captures real-time location, speed, and acceleration for every player on every play, but the public site mostly exposes aggregates and selected visualizations, not the full raw x/y tracking feed.
- Access: public site, nflverse NGS mirrors, and `nflreadr::load_nextgen_stats()` for weekly player-level passing/rushing/receiving NGS since 2016.
- Storage recommendation: store NGS aggregates by `season`, `week`, `player_id`, `stat_type`, and source extraction date.

### 7. NFL Big Data Bowl datasets

- NFL operations page: https://operations.nfl.com/gameday/analytics/big-data-bowl/
- Kaggle examples:
  - https://www.kaggle.com/competitions/nfl-big-data-bowl-2026-analytics
  - https://www.kaggle.com/competitions/nfl-big-data-bowl-2026-prediction
- What it gives you: player-tracking samples and challenge-specific labels. Recent competitions include pre-snap tendencies, pass-play movement, special teams, tackling, and other tracking problems.
- Access: Kaggle download, typically requiring acceptance of competition rules.
- Storage recommendation: store raw files unchanged. Build derived tables separately. Never overwrite competition raw data.

### 8. Pro Football Reference / Sports Reference

- URL: https://www.pro-football-reference.com/
- What it gives you: historical player stats, team stats, game logs, standings, awards, attendance and stadium-related information, and older historical context.
- Access: web tables and paid Stathead tools.
- Storage recommendation: use carefully and respect terms. Prefer it for validation, historical enrichment, and old seasons not fully covered by play-level modern feeds.

### 9. OverTheCap

- URL: https://overthecap.com/
- What it gives you: NFL contracts, cap hits, cash spending, dead money, positional spending, team cap space, restructures, and salary-cap analysis.
- Access: public web pages; `nflreadr::load_contracts()` loads historical player contracts from OverTheCap.
- Storage recommendation: store contract snapshots and normalize into contract-year tables. Contract data is often revised after restructures and designations.

### 10. Spotrac

- URL: https://www.spotrac.com/nfl/
- What it gives you: real-time contract lists, guaranteed money, salary breakdowns, cap tables, team payroll, transactions, and salary rankings.
- Access: public pages and paid products.
- Storage recommendation: store snapshots when using it for cap/business models.

### 11. NFLPA Public Salary Cap Report

- URL: https://nflpa.com/reports/public-salary-cap-report
- What it gives you: official public cap report, top-51 league cap report, team current contracts, carryover, adjustments, dead money, effective cap room, and active cap spending.
- Access: public web report.
- Storage recommendation: daily or weekly snapshot if modeling cap state over time. The report is generated daily and changes as contracts and roster moves occur.

### 12. Betting lines and market data

- Sources: nflverse schedules, sportsbooks, odds APIs, historical line datasets.
- What it gives you: spread, total, moneyline, and market-implied team strength.
- Why it matters: betting markets are strong aggregate priors for team strength, injuries, rest, travel, and public/private information.
- Storage recommendation: store open, close, source, and timestamp. Closing line value is not the same as an early-week line.

### 13. Weather and stadium data

- Sources: nflverse schedules, stadium metadata, public weather APIs, official gamebooks where available.
- What it gives you: roof, surface, temperature, wind, precipitation, stadium, neutral site, altitude.
- Why it matters: affects passing, kicking, scoring totals, play-calling, injury risk, and pace.
- Storage recommendation: store official schedule weather fields plus any external weather snapshots by game and timestamp.

## Practical answer: do you need to store data?

Yes. For serious football sabermetrics, store data even when the source is easy to reload.

Reasons:

1. Reproducibility: EPA, WP, contracts, IDs, injuries, and participation tables can be updated or corrected.
2. Performance: play-by-play and tracking samples are large enough that repeated remote reads slow development.
3. Joins: football analysis requires joining games, plays, rosters, contracts, injuries, participation, and market data.
4. Auditing: model outputs should identify exactly which data version produced them.
5. Backtesting: you need point-in-time extracts for betting, injury, salary, and depth-chart models.

## Minimum recommended raw NFL extract set

- `nfl_pbp`
- `nfl_schedules`
- `nfl_rosters`
- `nfl_players`
- `nfl_weekly_player_stats`
- `nfl_team_stats`
- `nfl_participation`
- `nfl_snap_counts`
- `nfl_injuries`
- `nfl_depth_charts`
- `nfl_draft_picks`
- `nfl_combine`
- `nfl_contracts`
- `nfl_nextgen_passing`
- `nfl_nextgen_receiving`
- `nfl_nextgen_rushing`
- `nfl_betting_lines`
- `nfl_stadium_weather`
- `nfl_big_data_bowl_tracking_samples`

## Recommended ingestion pattern

1. Pull each public source through the highest-quality package loader or official download path.
2. Write raw data to immutable Parquet by source and extraction date.
3. Create conformed IDs using nflverse player IDs, GSIS IDs, ESPN IDs, PFR IDs, and team aliases.
4. Build cleaned marts at the game, play, team-game, player-game, and player-on-play grain.
5. Save model inputs separately from raw data.
6. Record source version, pull date, package version, and transformation git SHA.
