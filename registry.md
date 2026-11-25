# registry.md — Code, Libraries & Tools (Sports/Football)

> Inventory of every repo, package, and tool incorporated into this vertical, with
> **license**, language, role, and status. Agents must consult this before adding a new
> dependency. License obligations are summarized here and enforced in `CLAUDE.md` §5.
> Data-source licensing lives in `public-data-sources.md`.
> **Last updated:** 2026-07-08

---

## 0. The core distinction (read first)

A permissive **code** license (e.g. MIT on an nflverse package) does **not** grant rights
to the **data** that code retrieves. Evaluate them separately. Savepoint's posture:

> **Sell/publish derived analysis, models, and visualizations. Never resell or
> redistribute a source's raw data or bulk-scraped tables. Always attach required
> attributions.**

---

## 1. NFL data-access packages (nflverse)

| Repo / Package | Lang | License | Status | Role |
|---|---|---|---|---|
| [nflverse/nflfastR](https://github.com/nflverse/nflfastR) | R | **MIT** | Active | Play-by-play with EPA, WP, CP, CPOE, YAC fields; PBP back to 1999. |
| [nflverse/nflreadr](https://github.com/nflverse/nflreadr) | R | **MIT** | Active | Loaders + dictionaries: schedules, rosters, stats, contracts, injuries, snap counts, participation, combine, draft, QBR, NGS. |
| [nflverse/nfl_data_py](https://github.com/nflverse/nfl_data_py) | Python | **MIT** | Active | Python access to PBP, weekly/seasonal, rosters, schedules, combine, IDs, draft. |
| [nflverse/nflreadpy](https://github.com/nflverse/nflreadpy) | Python | **MIT** | Active | Polars-native Python port of `nflreadr`. Preferred for new Python-first ingestion. |
| [nflverse/nflverse-data](https://github.com/nflverse/nflverse-data) | data | community releases | Active | Release files (CSV/Parquet/RDS/QS) behind the loaders — snapshot what you use. |

> **nflverse note:** open-source community project. Use freely for analysis; attribute
> nflverse; store versioned snapshots. Do **not** republish the full raw release files as
> your own dataset. Pin package versions — loader schemas evolve.

## 2. NCAA / college football data-access packages

| Repo / Package | Lang | License | Status | Role |
|---|---|---|---|---|
| [sportsdataverse/cfbfastR](https://github.com/sportsdataverse/cfbfastR) | R | **MIT** | Active | Tidy CFBD + ESPN wrapper; adds EPA/WP/PPA fields to play-by-play. |
| [CFBD/cfbd-python](https://github.com/CFBD/cfbd-python) | Python | **MIT** | Active | Official Python client generated from the CollegeFootballData OpenAPI spec. **Requires API key.** |

## 3. Reference / to-evaluate

| Repo / Tool | Lang | License | Status | Role |
|---|---|---|---|---|
| [nflWAR (Yurko et al.)](https://arxiv.org/abs/1802.00998) | R (paper+code) | check repo license before reuse | Reference | Methodology baseline for public-data WAR; reimplement, don't copy unlicensed code. |
| NFL Big Data Bowl notebooks (Kaggle) | Python/R | per-competition / per-author | Reference | Tracking-model ideas; respect competition rules and notebook licenses. |
| `sportsdataverse` ecosystem (hoopR, etc.) | R/Python | MIT | Reference | Sibling packages; consistent patterns across sports. |

> **No-license repos = all rights reserved.** Read for ideas; reimplement from scratch;
> do not copy source into a deliverable without written permission.

## 4. Recommended tech stack (Python-centric, R where useful)

| Layer | Choice | License | Why |
|---|---|---|---|
| Object storage (raw) | **MinIO** (or S3) | AGPLv3 (self-host OK) / AWS | S3-compatible landing zone for raw Parquet/JSON, date/season-partitioned. |
| Warehouse (curated) | **PostgreSQL** (or DuckDB for local) | PostgreSQL / MIT | Conformed dims, facts, features, model outputs; serving/BI. |
| Local OLAP engine | **DuckDB** | MIT | Query Parquet directly (`httpfs`) for heavy feature work without bloating Postgres. |
| Transformation | **dbt-core** (`dbt-postgres` / `dbt-duckdb`) | Apache-2.0 | Versioned, tested, documented transforms; medallion modeling. |
| Orchestration | **Dagster** (or **Prefect**; cron+Make to start) | Apache-2.0 | Asset pipelines with lineage; lightweight for solo ops. |
| DataFrames | **Polars** + **pandas** + **PyArrow** | MIT / BSD / Apache | Polars for large PBP/participation; Arrow/Parquet interchange. |
| Linear algebra | **NumPy** | [BSD-3-Clause](https://numpy.org/doc/stable/license.html) | Fit and resample the opponent-adjusted efficiency model. |
| Modeling | **scikit-learn, XGBoost, LightGBM, statsmodels** | BSD / Apache / MIT | Outcome models, ratings, adjusted plus-minus (ridge/elastic-net). |
| Bayesian | **PyMC / bambi** | Apache-2.0 | Hierarchical player rates, partial pooling, counterfactuals. |
| Data validation | **Pandera** (or Great Expectations) | MIT / Apache | Quality gates on ingested tables. |
| Experiment tracking | **MLflow** | Apache-2.0 | Model versions, metrics, calibration history. |
| Serving / BI | **Streamlit** (+ **Metabase**) | Apache / AGPL | Dashboards + ad-hoc BI over Postgres. |
| Python env | **uv** (or Poetry) | MIT / Apache | Fast, reproducible deps + lockfile. |
| R env | **renv** + `nflreadr` / `cfbfastR` | MIT | Reproducible R for the R-only loaders. |
| Containers | **Docker Compose** | Apache-2.0 | Run Postgres + MinIO + orchestrator locally / on a lab box. |

## 5. License compliance summary (code)

- **Permissive (MIT/BSD/Apache):** all nflverse packages, cfbfastR, cfbd-python, DuckDB,
  dbt, Dagster, Prefect, scikit-learn, XGBoost, LightGBM, statsmodels, PyMC, Pandera,
  MLflow, Polars, uv — free for commercial use; retain copyright/license notices.
- **Copyleft (AGPLv3):** MinIO server, Metabase — fine to self-host and use unmodified;
  AGPL network-service obligations trigger only if you distribute a *modified* version as
  a service.
- **No license / all-rights-reserved:** any reference repo without a `LICENSE` — reference
  only; no code reuse without permission; reimplement concepts from scratch.

> The harder compliance question is the **data**, not the code. See
> `public-data-sources.md` and `CLAUDE.md` §5.

## 6. Rule for adding anything new

1. Add the repo/package/tool to this file with **language + license + role** before use.
2. If it retrieves data, also add the **data source** to `public-data-sources.md` with
   its ToS, rate limit, and attribution.
3. Pin the version (loaders and scrapers change without notice).
