# CLAUDE.md — Operating Rules for Agents (Sports/Football)

> Read order: `../../COMPANY_CONTEXT.md` → `../CLAUDE.md` (sports vertical brief) →
> `COMPANY_CONTEXT.md` → `PROJECT_CONTEXT.md` → this file.
> This is the constitution for any AI agent working in the American football
> (NFL + NCAA) vertical. The tool-agnostic mirror of these rules lives in `AGENTS.md`.
> Domain detail lives in `docs/` and `README.md`.
> **Last updated:** 2026-07-08

---

## 1. Mission in one sentence

Build a reproducible, public-data-first American football sabermetrics platform —
NFL first, then NCAA — that estimates team, player, coach, and roster value from
play-level changes in expected points and win probability, connects those estimates
to wins, salary/cap efficiency, and program revenue, and does so while strictly
honoring data licensing so the output can be published or sold legally.

## 2. Golden rules

1. **Reproducibility over cleverness.** Every metric must trace from raw source →
   transform → output and re-run from a clean checkout. EPA/WPA, contracts, IDs,
   injuries, and participation tables all get revised upstream — store versioned
   snapshots (see §4).
2. **Label the claim.** Every analysis and every model output is one of:
   *descriptive*, *predictive*, *causal*, *counterfactual/simulation*, or
   *valuation/economic estimate*. Never let a descriptive number masquerade as causal.
3. **Uncertainty is not optional.** EPA and WP are model outputs, not ground truth.
   Report intervals, calibrate by season and game state, and never present a tiny
   EPA/WP gap as definitive.
4. **Don't over-credit the ball-carrier.** Football is 22-player interdependence.
   Use teammate/opponent controls, participation data, and position-specific
   replacement baselines. OL/DL/LB/DB public estimates are impact *proxies*, not grades.
5. **Compliance is non-negotiable.** Never use a data source in a way that violates
   §5. When unsure, stop and ask.
6. **Python-first.** Analysis, transforms, pipelines, automation = Python. Use R only
   where it is clearly better (e.g. `cfbfastR`, `nflreadr` functions absent in the
   Python ports).
7. **Sell insight, not raw data.** Deliverables are derived analysis, models, and
   visuals — never repackaged proprietary feeds or bulk-scraped tables.

## 3. Tech-stack conventions

- **Language:** Python ≥ 3.11, managed with **uv** (lockfile committed). R via **renv**
  for `nflreadr`/`cfbfastR`-only tasks.
- **DataFrames:** Polars for large play-by-play/participation data; pandas where the
  ecosystem requires it; Parquet + PyArrow for interchange. `nflreadpy` is Polars-native.
- **Transforms:** **dbt** models (medallion: raw → staging → core → analytics/features/
  models, per `docs/08-public-data-warehouse-design.md`). SQL transforms are tested and
  documented.
- **Orchestration:** **Dagster** or **Prefect** assets (start with cron + Make if that
  is overkill early).
- **Modeling:** scikit-learn / XGBoost / LightGBM / statsmodels; **PyMC / bambi** for
  hierarchical player rates and partial pooling; ridge/elastic-net for adjusted
  plus-minus. Track runs in **MLflow**.
- **Validation:** **Pandera** schemas (or Great Expectations) gate every ingested table.
- **Style:** `ruff` (lint+format), `mypy` for typed modules, `pytest` for tests.
  Notebooks are for exploration only — production logic lives in `src/`.

## 4. Storage architecture

**Public data must be snapshotted even when it is easy to reload.** Play-by-play,
participation, contracts, injuries, IDs, and finance tables all change or get
backfilled; models must be rebuildable from the exact bytes that produced them.

Recommended layering (full schema in `docs/08-public-data-warehouse-design.md`):

- **`raw`** — immutable source extracts, partitioned by `league` and `season` (or
  `snapshot_date` for changing data: contracts, cap, injuries, depth charts, betting
  lines). Parquet in object storage (MinIO/S3) or a local lake; never edited in place.
- **`staging`** — normalize column names, types, team aliases; preserve source IDs and
  source date/version columns. No derived features yet.
- **`core`** — conformed dims and facts: `dim_league / dim_team / dim_game / dim_player /
  dim_venue / dim_school`; `fact_play`, `fact_player_on_play`, `fact_team_game`,
  `fact_player_game`, `fact_contract_year`, `fact_school_finance_year`.
- **`analytics` / `features` / `models` / `finance`** — marts, frozen model inputs, and
  model outputs (with `model_run_id`, version, training window, intervals, calibration).
- **`metadata`** — extract log, data dictionary, ID-resolution log, model-run log,
  known source limitations.

Maintain explicit **ID bridges** (`bridge_player_ids`, `bridge_team_ids`) across
nflverse/GSIS/PFR/ESPN/CFBD/recruiting IDs — football player identity is unstable.

**Local/prototype:** Parquet + DuckDB + dbt-duckdb. **Scalable:** MinIO/S3 + Postgres
(or DuckDB/Snowflake/BigQuery), dbt, Prefect/Dagster, MLflow. Keep secrets (CFBD API
key, etc.) in `.env` (git-ignored); never commit credentials.

## 5. Compliance rules (MUST follow) — and why

These derive from `public-data-sources.md`, `registry.md`, and `docs/`. Document the
reason in code comments when a rule shapes an implementation.

**Data-source rules:**
- **nflverse (nflfastR / nflreadr / nfl_data_py / nflreadpy)** — ✅ open-source
  community data over public release files; use freely for analysis. Credit nflverse.
  Store versioned snapshots; do **not** re-publish the full raw release files as your
  own dataset. *Why: it is a public good maintained by volunteers — attribute and don't
  masquerade their releases as yours.*
- **CollegeFootballData.com / cfbfastR / cfbd-python** — ⚠️ **API key required**;
  respect the CFBD terms, tiering, and rate limits; attribute CollegeFootballData.
  Cache responses; do not hammer the API for data you already snapshotted. *Why: CFBD
  is a small operation offering a free/patron API under its own terms.*
- **NFL Next Gen Stats** — ⚠️ public site exposes **aggregates only**; the full raw
  x/y tracking feed is **not** public. Access NGS aggregates via `nflreadr::load_nextgen_stats()`
  or nflverse mirrors; do not imply you have raw tracking. Credit NFL/NGS.
- **NFL Big Data Bowl (Kaggle)** — ⚠️ governed by **competition rules** you must accept
  to download. Store raw files unchanged; use for research/portfolio. Check each
  competition's rules before any commercial use.
- **Pro Football Reference / Sports Reference (CFB)** — ⚠️ scraping is rate-limited
  (**≤ 20 requests/min**, ≤ 10 for Stathead) and bulk-scrape-backed products / AI
  training on scraped data are prohibited; attribute Sports Reference LLC. Prefer
  nflverse/CFBD for systematic pulls; use SR for validation and old seasons only.
- **OverTheCap / Spotrac** — ⚠️ contract/cap data; prefer `nflreadr::load_contracts()`
  (OverTheCap-sourced) for historical contracts; snapshot by date; attribute the source.
  Do not redistribute their full contract database as a product.
- **NFLPA Public Salary Cap Report** — ✅ public report; snapshot by date (generated daily).
- **Betting lines / market data** — ⚠️ store open, close, source, and timestamp; use as
  a **strong benchmark/feature, never as ground truth**. Keep gambling-adjacent framing
  cautious, legal, and secondary to sport understanding.
- **EADA / Knight-Newhouse / USA Today NCAA finances** — ✅ public finance data;
  version by fiscal year; **reconcile differing accounting definitions** before mixing.
- **NCAA player compensation** — ❗ there is **no** complete, audited, public player-level
  salary table. Treat all of it as **estimation, not measurement** (see §6).

**Code-license rules:**
- **Permissive deps (nflverse packages, cfbfastR, cfbd-python, DuckDB, dbt, Dagster,
  Prefect, scikit-learn…)** — ✅ commercial OK; retain copyright/license notices.
  Record each in `registry.md` with its license **before** use.
- **Copyleft / no-license repos** — if a reference repo has no license, it is
  all-rights-reserved: read for ideas, reimplement from scratch, do not copy code into a
  deliverable without written permission.

**Operational guardrails for agents:**
- Centralize every source's attribution string (nflverse, CFBD, NGS, PFR/SRL, OverTheCap)
  in `src/compliance/attributions.py` and auto-stamp it onto exported reports/dashboards.
- Enforce rate limits and caching in the ingestion layer (shared throttle/backoff).
- If a task would require violating any rule above (e.g. "bulk-scrape PFR into a sellable
  table" or "publish NIL valuations as actual salaries"), **refuse and propose a
  compliant alternative.**

## 6. Football-specific analysis standards

### Always do
- Lead with **EPA** for stability and **WPA** for leverage/game-management; use
  **success rate** and **explosive-play rate** for consistency vs. big-play identity.
- Use **CPOE** over raw completion % for QB accuracy; **PPA** as the CFB analogue to EPA.
- Opponent-adjust everything for NCAA (conference/schedule imbalance is huge); include
  conference-year effects and handle garbage time.
- Use **shrinkage / hierarchical partial pooling** for small samples (17 NFL games,
  ~12 CFB games; linemen, DBs, backups have tiny samples).
- Report replacement baselines by **position and role**; present participation-based
  plus-minus as a **lineup-impact proxy** with wide intervals.
- For fourth-down / two-point / FG-punt-go decisions, output **go/kick/punt with
  confidence bands** and label toss-ups honestly; evaluate coaches against an
  uncertainty-aware decision frontier, and distinguish a *bad decision* from a
  *conservative objective function*.
- Separate **cap hit vs. cash vs. guarantees vs. dead money** — they answer different
  questions; never use AAV alone. Snapshot contracts by date; account for restructures
  and void years.

### Never do
- Rank players by raw yards/game, raw TDs, or **QB wins**.
- Treat EPA as causal without accounting for play selection, or treat a 0.2pp WP edge
  as definitive.
- Present OL/DL/LB/DB public estimates as definitive individual grades.
- Equate **NIL valuations with actual compensation**, or collapse scholarship + direct
  pay + NIL into one "salary" field.
- Treat NFL Forbes revenue/valuations as audited, or betting markets as truth.
- Infer individual medical diagnoses from public injury data (games-missed/status are
  proxies only). Keep health/labor-economics work aggregate and non-sensational.

## 7. NCAA compensation guardrail

NCAA work operates in the **post–*House v. NCAA*** environment: schools may directly
share revenue (initial 2025-26 cap ≈ $20.5M/institution) and athletes may earn NIL,
but verified player-level compensation is not cleanly public. Therefore:

- Frame compensation as **estimated / reported / implied market value**, always as
  **low/mid/high ranges** with a confidence score — never single-point "salary".
- Keep components separate: scholarship value, cost-of-attendance, direct revenue-share
  estimate, NIL (cash / non-cash), benefits.
- Build the **performance side first** (it is far stronger than the compensation side),
  then layer compensation as a range-based economic estimate with explicit caveats and
  Title IX / legal-uncertainty notes.

## 8. Working agreements

- Small, reviewable changes; conventional commits.
- New dependency → add to `registry.md` with its license before use.
- New data source → add to `public-data-sources.md` (ToS + attribution + rate limit)
  before use.
- Write tests for transforms and modeling utilities; validate data with Pandera.
- Prefer explicit, documented SQL/dbt over hidden notebook logic.
- When a technique generalizes (adjusted plus-minus, hierarchical rates, decision-policy
  simulation), note it for the shared methodology layer so other sports can borrow it.

## 9. Cross-vertical connections

| This vertical | Connects to | How |
|---|---|---|
| Adjusted plus-minus / on-field value | Basketball (RAPM), Soccer (VAEP) | Same regularized player-effect design matrix |
| WAR / replacement value | Baseball (WAR), Basketball (EPM/BPM) | Points-to-wins conversion + role baselines |
| AI Coach decision simulation | Board Game AI | Sequential decision under uncertainty, MDP / offline policy eval |
| Contract / cap surplus modeling | Game Analytics (economy), Economics | Value-per-cost, salary efficiency |
| Revenue & health-cost labor economics | Economics | Panel data, fixed effects, event studies, DiD |
| Recruiting / draft value | Baseball (prospect), Economics (human capital) | Survival + development curves |

## 10. Pointers

- Project goals & phase: `PROJECT_CONTEXT.md`
- Sports vertical brief (all sub-sports): `../CLAUDE.md`
- Company mission & constraints: `../../COMPANY_CONTEXT.md` and `COMPANY_CONTEXT.md`
- Tool-agnostic agent rules: `AGENTS.md`
- Dependencies + licenses: `registry.md`
- Data catalog + ToS + attribution: `public-data-sources.md`
- Domain deep-dives (data sources, methods, player value, warehouse, roadmap,
  limitations, research extensions): `docs/` (see `README.md` for the index)
- Build/run + layout: `README.md`
