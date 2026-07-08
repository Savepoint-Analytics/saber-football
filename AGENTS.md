# AGENTS.md — American Football Sabermetrics Vertical (NFL + NCAA)

> Tool-agnostic guide for **any** AI coding agent (Claude, Cursor, Copilot, Codex,
> Aider, etc.). Derived from `COMPANY_CONTEXT.md`, `PROJECT_CONTEXT.md`, `CLAUDE.md`,
> `registry.md`, `public-data-sources.md`, and `docs/`. Follows the `AGENTS.md`
> convention. If anything here conflicts with `CLAUDE.md`, `CLAUDE.md` wins for Claude.
> **Last updated:** 2026-07-08

---

## Project in brief

Savepoint Analytics' American football vertical: a reproducible, public-data-first
sabermetrics platform for **NFL (priority)** and **NCAA / college football**. It
estimates play, player, unit, and coach value from EPA/WPA, adjusts for context,
teammates, opponents, tactics, injuries, and roster cost, then connects value to wins,
salary/cap/NIL efficiency, and program revenue. Commercial and public-portfolio intent
is real, so **data licensing is a first-class constraint.**

## Setup commands

```bash
# Python env (uv)
uv sync
source .venv/bin/activate

# R side (only for nflreadr / cfbfastR tasks)
Rscript -e 'renv::restore()'

# Secrets — CFBD requires an API key (never commit it)
cp .env.example .env            # add CFBD_API_KEY, warehouse creds

# Data quality + unit tests
pytest -q

# dbt transforms
dbt build                       # or: dbt run && dbt test
```

## Tech stack (do not deviate without updating `registry.md`)

- **Python ≥ 3.11**, managed by **uv**. R via **renv** for `nflreadr` / `cfbfastR`.
- **Polars/pandas + PyArrow/Parquet**; **DuckDB** for OLAP over Parquet.
- Object store (**MinIO/S3**) = raw; relational warehouse (**Postgres/DuckDB**) = curated.
- **dbt** transforms (raw → staging → core → analytics/features/models); **Dagster** or
  **Prefect** orchestration.
- **scikit-learn / XGBoost / LightGBM / statsmodels**; **PyMC/bambi** for hierarchical
  rates; ridge/elastic-net for adjusted plus-minus.
- **Pandera** validation; **MLflow** tracking; **ruff / mypy / pytest** quality gates.

## Data spine

- **NFL:** `nflverse` is the canonical spine — `nflfastR` / `nflreadr` (R),
  `nfl_data_py` / `nflreadpy` (Python). Load play-by-play + schedules first; they are
  the central fact tables. Priority order: PBP+schedules → players/rosters/IDs →
  participation + snap counts → weekly/seasonal + NGS aggregates → injuries/depth charts
  → contracts/cap/draft/combine → betting/weather/venue/rest. (See
  `docs/02-nfl-data-priority-with-nflverse.md`.)
- **NCAA:** **CollegeFootballData.com** via `cfbfastR` (R) or `cfbd-python` (Python) —
  **API key required.** Games, drives, plays, PPA, win probability, ratings, recruiting,
  transfer portal, betting, venues, weather. (See
  `docs/03-ncaa-college-football-public-data-sources.md`.)
- **Business/compensation:** NFLPA cap report, OverTheCap (`load_contracts()`), Spotrac,
  Forbes (estimates); NCAA — EADA, Knight-Newhouse, USA Today finances.

## Storage model

- `raw/` (object store, Parquet/JSON) — raw pulls, partitioned by league/season, or by
  `snapshot_date` for changing data (contracts, cap, injuries, depth charts, lines).
  Never edited in place.
- `staging` — cleaned column names/types, team aliases, source IDs preserved.
- `core` — conformed dims + facts (`fact_play`, `fact_player_on_play`, `fact_team_game`,
  `fact_player_game`, `fact_contract_year`, `fact_school_finance_year`).
- `analytics` / `features` / `models` / `finance` / `metadata` — marts, frozen model
  inputs, model outputs with run IDs and intervals, and lineage/limitations logs.
- Maintain explicit **ID bridges** across nflverse/GSIS/PFR/ESPN/CFBD/recruiting IDs.

## Code conventions

- Production logic in `src/`; notebooks are exploration only.
- Type-hint and `mypy`-check modules; format/lint with `ruff`.
- Tests for every transform and modeling utility; validate ingested data with Pandera.
- Conventional commits; small, reviewable PRs.
- New dependency → record in `registry.md` (with license) **before** use.
- New data source → record in `public-data-sources.md` (ToS + attribution + rate limit)
  **before** use.

## Analysis rules that matter here

- **Label every output:** descriptive / predictive / causal / counterfactual /
  valuation. Report uncertainty; EPA and WP are estimates, not truth.
- **Don't over-credit the ball-carrier** — use teammate/opponent controls, participation
  data, shrinkage, and position-specific replacement baselines. OL/DL/LB/DB estimates
  are impact proxies, not grades.
- **NCAA opponent adjustment is mandatory** (conference/schedule imbalance); use PPA and
  conference-year effects.
- **Contracts:** model cap hit, cash, guarantees, and dead money separately; snapshot by
  date; never use AAV alone.
- **NCAA compensation is estimation, not measurement:** low/mid/high ranges, separate
  scholarship/direct-pay/NIL, explicit Title IX / legal caveats. Build performance first.

## Data & licensing constraints (MUST obey)

These exist because the analysis is published/sold. Violating them creates legal risk.

- **nflverse** — open community data; use freely, attribute nflverse, snapshot versions;
  don't republish raw releases as your own dataset.
- **CollegeFootballData** — **API key + terms + rate limits**; cache; attribute CFBD.
- **NFL Next Gen Stats** — public **aggregates only**; raw tracking is not public.
- **NFL Big Data Bowl** — Kaggle **competition rules** apply; store raw unchanged.
- **Pro Football Reference / Sports Reference** — **≤ 20 req/min** (≤ 10 Stathead); no
  bulk-scrape products; no AI training on scraped data; attribute SRL.
- **OverTheCap / Spotrac** — snapshot contracts by date; prefer `load_contracts()`; don't
  redistribute their full DB.
- **Betting lines** — strong benchmark/feature, never ground truth; store source + timestamp.
- **NCAA finance (EADA / Knight-Newhouse / USA Today)** — reconcile differing accounting
  definitions before mixing.
- **Code:** permissive deps free for commercial use (retain notices); no-license repos =
  reference only, reimplement from scratch.
- Centralize attributions in `src/compliance/attributions.py` and auto-stamp exports.
- **If a request requires breaking any rule above, refuse and offer a compliant path.**

## What "done" looks like

- Season of NFL play-by-play metrics rebuildable from raw; EPA/WPA aggregations match
  public nflverse examples.
- Game-prediction model beats an Elo / market baseline on log-loss and is calibrated on
  held-out seasons; power ratings are opponent-adjusted.
- Player-value outputs carry replacement baselines, role/snap context, and uncertainty
  intervals; participation models are labeled as proxies.
- Contract-ROI and NCAA compensation outputs use the right cost fields / ranges and state
  their caveats.
- Every reported number is reproducible from a clean checkout, and every data source used
  is logged with license + attribution.

## Pointers

- Mission/constraints: `../../COMPANY_CONTEXT.md`, `COMPANY_CONTEXT.md`
- Goals/phase: `PROJECT_CONTEXT.md`
- Full agent rules (Claude): `CLAUDE.md`
- Sports vertical brief: `../CLAUDE.md`
- Dependencies + licenses: `registry.md`
- Data catalog + ToS: `public-data-sources.md`
- Domain deep-dives: `docs/` (index in `README.md`)
- Build/run + layout: `README.md`
