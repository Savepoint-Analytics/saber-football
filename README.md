# Savepoint Analytics — American Football Sabermetrics (NFL + NCAA)

Reproducible, public-data-first American football analytics: estimate team, player, unit,
and coach value from play-level **expected points (EPA)** and **win probability (WPA)**,
adjust for context, teammates, opponents, tactics, injuries, and roster cost, then connect
those estimates to **wins, salary/cap & NIL efficiency, and program revenue** — and
simulate counterfactual coaching with an **AI Coach**. Built as a sub-vertical of
[Savepoint Analytics](../../COMPANY_CONTEXT.md), extending the
[baseball flagship](../baseball/README.md) into the NFL and college football.

Last updated: 2026-11-21

> **Status** — Phase 1 NFL prototype. Rebuilt 2024 and 2025, covering 285 games and 32 teams each.
> The play-by-play warehouse produces a descriptive team-style mart and Streamlit dashboard,
> and the player-context build produces team and player dimensions, an ID bridge, snap counts,
> and on-field participation. Player-context quality reports are available for both seasons.
> See `PROJECT_CONTEXT.md` §14.

> **New here? Read in this order:** `../../COMPANY_CONTEXT.md` → `../CLAUDE.md`
> (sports brief) → `COMPANY_CONTEXT.md` → `PROJECT_CONTEXT.md` → `CLAUDE.md`
> (or `AGENTS.md`) → `registry.md` → `public-data-sources.md`, then the `docs/` suite.

---

## Core thesis

> Estimate team and player value from play-level changes in expected points and win
> probability, adjust for context, teammates, opponents, tactics, injuries, and roster
> cost, then connect those estimates to wins, salary efficiency, and team/program revenue.

The goal is not only to describe who played well, but to estimate which players, tactics,
coaches, roster decisions, and compensation choices actually move wins, efficiency, health
risk, and business value — from public or semi-public data rather than a proprietary feed
at the outset.

## Why this project exists

American football is a 22-player, high-interdependence, low-sample, role-specialized
sport, so baseball-style isolated-event valuation does not transfer directly. The public
data ecosystem is now strong enough — **nflverse** for the NFL, **CollegeFootballData** for
NCAA — to do serious play-level, player, tactical, roster-economics, and finance modeling,
provided the work is uncertainty-aware and license-compliant. This vertical proves the
Savepoint multi-sport engine extends cleanly from baseball to football and adds a
distinctive centerpiece: an AI Coach decision simulator.

## Documentation & agent context

**Agent-context files (read in the order above):**

| File | Purpose |
|---|---|
| `../../COMPANY_CONTEXT.md` | Global Savepoint business & founder source of truth. |
| `../CLAUDE.md` | Sports-sabermetrics **vertical** brief (all sub-sports). |
| `COMPANY_CONTEXT.md` | Football-specific business positioning, audiences, offers, and boundaries. |
| `PROJECT_CONTEXT.md` | Longitudinal project record: objective, scope, phase, decisions, data, open questions, priorities. |
| `CLAUDE.md` | Operating constitution for AI agents — golden rules, tech/storage conventions, compliance, analysis standards. |
| `AGENTS.md` | Tool-agnostic mirror of `CLAUDE.md` for any coding agent. |
| `registry.md` | Code/library/tool inventory with licenses. |
| `public-data-sources.md` | Data catalog with ToS, rate limits, and required attribution. |

**Domain deep-dives (`docs/`):**

1. [`docs/01-nfl-public-data-sources.md`](docs/01-nfl-public-data-sources.md) — NFL public data sources, access patterns, storage/API expectations.
2. [`docs/02-nfl-data-priority-with-nflverse.md`](docs/02-nfl-data-priority-with-nflverse.md) — recommended NFL ingestion priority, centered on nflverse.
3. [`docs/03-ncaa-college-football-public-data-sources.md`](docs/03-ncaa-college-football-public-data-sources.md) — NCAA / college football data sources.
4. [`docs/04-public-research-and-football-methods.md`](docs/04-public-research-and-football-methods.md) — public research and methods that apply to American football.
5. [`docs/05-player-value-models.md`](docs/05-player-value-models.md) — player evaluation, WAR, plus-minus, salary-efficiency modeling.
6. [`docs/06-ncaa-compensation-caveat.md`](docs/06-ncaa-compensation-caveat.md) — NCAA compensation, NIL, revenue sharing, data caveats.
7. [`docs/07-revenue-salaries-business-performance-data.md`](docs/07-revenue-salaries-business-performance-data.md) — NFL/NCAA salary, revenue, finance, business data.
8. [`docs/08-public-data-warehouse-design.md`](docs/08-public-data-warehouse-design.md) — recommended public-data warehouse design.
9. [`docs/09-modeling-roadmap.md`](docs/09-modeling-roadmap.md) — roadmap from descriptive metrics to simulation and economics.
10. [`docs/10-limitations.md`](docs/10-limitations.md) — limitations, bias risks, and what public data cannot answer alone.
11. [`docs/11-research-extensions.md`](docs/11-research-extensions.md) — AI Coach simulation, health-cost labor economics, NCAA hockey/player-compensation estimation.

## Source strategy

Use official and project-maintained public sources first:

- **NFL backbone:** [nflverse](https://nflverse.nflverse.com/) — [nflfastR](https://nflfastr.com/), [nflreadr](https://nflreadr.nflverse.com/), [nfl_data_py](https://github.com/nflverse/nfl_data_py), [nflreadpy](https://github.com/nflverse/nflreadpy).
- **NCAA backbone:** [CollegeFootballData.com](https://collegefootballdata.com/) ([API](https://api.collegefootballdata.com/)), [cfbfastR](https://cfbfastr.sportsdataverse.org/), [cfbd-python](https://github.com/CFBD/cfbd-python) — **API key required**.
- **Tracking samples:** [NFL Big Data Bowl](https://operations.nfl.com/gameday/analytics/big-data-bowl/) (Kaggle) — competition rules apply.
- **Business & compensation:** [NFLPA cap report](https://nflpa.com/reports/public-salary-cap-report), [OverTheCap](https://overthecap.com/), [Spotrac](https://www.spotrac.com/nfl/), [EADA](https://ope.ed.gov/athletics/), [Knight-Newhouse](https://knightnewhousedata.org/), [USA Today NCAA finances](https://sportsdata.usatoday.com/ncaa/finances), Forbes NFL valuations.

Licensing, rate limits, and required attributions for every source live in
`public-data-sources.md`. **Rule of thumb: publish/sell the analysis, never the raw feed;
always attach attributions; cache and rate-limit.**

## Architecture & storage stance

Even when data is reachable through a loader or public URL, **store versioned snapshots.**
Football models are sensitive to data revisions, changing IDs, moving source definitions,
and historical backfills. A reproducible project supports raw immutable extracts →
cleaned/conformed tables → model-input feature marts → model-output tables (with run IDs)
→ source/version metadata → a clear rebuild path.

Recommended layering (full schema in `docs/08-public-data-warehouse-design.md`):

```
raw ──► staging ──► core ──► analytics / features / models / finance
 │        (normalize)   (dims + facts)     (marts, frozen model inputs,
 │                                          model outputs w/ run IDs + intervals)
 └─ immutable Parquet, partitioned by league/season (or snapshot_date for
    contracts, cap, injuries, depth charts, betting lines)
metadata ─ extract log · data dictionary · ID-resolution log · model-run log · limitations
```

- **Object store (MinIO/S3)** = raw landing zone for large play-by-play & participation.
- **Postgres / DuckDB** = curated warehouse (dims, facts, features, model outputs) for
  serving/BI; DuckDB for OLAP over Parquet.
- **dbt** = tested, documented transforms; **Dagster/Prefect** = orchestration;
  **MLflow** = model tracking. Local prototype: Parquet + DuckDB + dbt-duckdb.
- Maintain explicit **ID bridges** across nflverse/GSIS/PFR/ESPN/CFBD/recruiting IDs —
  football player identity is unstable.

## Proposed repository layout

```
football-sabermetrics/
├── README.md · CLAUDE.md · AGENTS.md
├── COMPANY_CONTEXT.md · PROJECT_CONTEXT.md
├── registry.md · public-data-sources.md
├── docs/                       # domain suite 01–11 (indexed above)
│
├── pyproject.toml              # uv-managed deps; generate uv.lock with `uv sync`
├── docker-compose.yml          # postgres + minio + orchestrator
├── .env.example                # config template incl. CFBD_API_KEY (never commit real .env)
├── Makefile                    # ingest / build / test / sim
│
├── src/
│   ├── ingestion/              # nfl_pbp.py, cfbd.py, contracts.py, _throttle.py (rate-limit+cache)
│   ├── compliance/attributions.py   # canonical attribution strings, auto-stamped on exports
│   ├── features/               # EPA/WPA aggregation, participation on/off, adjusted plus-minus
│   ├── models/                 # team ratings, player value, contract ROI, decision models
│   ├── simulation/             # AI Coach policy engine + counterfactual game/season sim
│   └── serving/                # Streamlit dashboards, report builders
│
├── dbt/models/{staging,core,analytics,features,models,finance}/
├── orchestration/              # Dagster/Prefect assets
├── r/                          # renv; nflreadr / cfbfastR helpers
├── notebooks/                  # exploration ONLY — no production logic
├── tests/                      # pytest: transforms, models, Pandera schemas
└── data/                       # local scratch (git-ignored; real data in object store / PG)
```

## Quickstart

```bash
# 1. Environment
uv sync --locked --extra dev --extra serving
test -f .env || cp .env.example .env
export SABER_STORAGE_BACKEND=local

# 2. Local infra (optional early)
docker compose up -d            # Postgres and MinIO

# 3. First NFL pull (nflverse play-by-play + schedules → immutable Parquet)
make ingest LEAGUE=nfl SEASON=2025

# 4. Transform + validate
make core SEASON=2025
make analytics SEASON=2025
make reconcile SEASON=2025
make test

# 5. Explore
make serve

# 6. Build the initial player-context tables for a completed season
make ingest-teams ingest-players ingest-rosters ingest-participation ingest-snap-counts SEASON=2025
make identity SEASON=2025
make player-quality SEASON=2025
```

### Rebuild a completed NFL season from pinned inputs

Use `SABER_STORAGE_BACKEND=local` for local ingestion. Once all seven inputs are present,
create a manifest and use it for the rebuild.

```bash
manifest=data/quality/season=2024/raw_manifest_local.json
make snapshot-manifest SEASON=2024 MANIFEST="$manifest"
make -j1 core identity analytics reconcile player-quality SEASON=2024 MANIFEST="$manifest"
```

Save this manifest alongside the retained snapshots. Each entry records a local path relative
to `SABER_DATA_DIR` or an S3 URI and a SHA-256 checksum. A pinned build stops if the raw bytes
have changed. The reconciliation reads the PBP pinned by the core build. Run the targets
in order for a given season.

For MinIO, configure the endpoint, credentials, bucket, and optional `MINIO_PREFIX`.
Ingest with `SABER_STORAGE_BACKEND=minio` or select a prefix holding previously retained
snapshots. Create the manifest with
`uv run python -m src.warehouse.snapshots --season 2024 --from-minio --output /path/to/manifest.json`.
Pass the manifest to the same build targets. They read the pinned MinIO objects directly and
write results under the local `SABER_DATA_DIR`.

The player-quality target writes a JSON summary, a team-game coverage Parquet file, and an
unresolved snap ID review under `data/quality/season=<season>/player_context/`. Participation
coverage measures analysis-play sides with any recorded players. A separate count records
sides with exactly 11 players. Roster names and teams surface candidate matches for review.

## Roadmap (condensed — full version in `docs/09-modeling-roadmap.md`)

1. **Phase 0 — Foundations:** context + docs, warehouse design, repo skeleton.
2. **Phase 1 — NFL warehouse + descriptive team analytics (current):** nflverse PBP → EPA/WPA/
   success/explosive → opponent-adjusted efficiency & style dashboards.
3. **Phase 2 — Player performance models:** QB, skill-position, special teams,
   participation-based on/off, opportunity.
4. **Phase 3 — Team strength & game prediction:** opponent-adjusted power ratings; win
   probability / margin / total vs. market baselines; calibration.
5. **Phase 4 — Player value & WAR + contract ROI:** points-above-replacement → wins →
   cap/cash surplus; rookie-contract surplus; positional market efficiency.
6. **Phase 5 — Tactical/coaching → AI Coach simulation:** decision models, then a policy
   engine replaying games under counterfactual decisions.
7. **NCAA + research extensions:** CollegeFootballData ingestion → team PPA → finance →
   range-based compensation; injury/health-cost labor economics; tracking-derived models.

## Data & licensing — the short version

The code we depend on is mostly MIT (free for commercial use). **The data is not the same
as the code.** Before using any source, check `public-data-sources.md`. Headlines:

- ✅ **nflverse** (derived analysis; attribute; snapshot versions) — the NFL foundation.
- ⚠️ **CollegeFootballData** — API key + rate limits; cache; attribute CFBD.
- ⚠️ **NFL Next Gen Stats** — public aggregates only; raw tracking is not public.
- ⚠️ **NFL Big Data Bowl** — Kaggle competition rules; store raw unchanged.
- ⚠️ **Pro Football Reference / Sports Reference** — ≤20 req/min, attributed, no bulk-scrape products.
- ⚠️ **OverTheCap / Spotrac** — snapshot contracts by date; don't redistribute their DB.
- ❗ **NCAA player compensation** — no verified public data; estimate as low/mid/high ranges.

Full obligations and the *reasons* are documented in `CLAUDE.md` §5, `AGENTS.md`, and
`public-data-sources.md`.

## Reporting discipline

Every analysis and model output is labeled as one of: **descriptive**, **predictive**,
**causal**, **counterfactual/simulation**, or **valuation/economic estimate** — and carries
data source, extraction date, model version, uncertainty, and known limitations. EPA and WP
are model outputs, not ground truth; public OL/DL/LB/DB estimates are impact proxies, not
grades; NIL valuations are not salaries. See `docs/10-limitations.md`.
