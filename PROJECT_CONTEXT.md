# PROJECT_CONTEXT.md — Sports / Football (NFL + NCAA Sabermetrics)

> **Vertical:** Sports → American Football (NFL primary, NCAA second)
> **Inherits:** `../../COMPANY_CONTEXT.md` → `../CLAUDE.md` → `COMPANY_CONTEXT.md`
> **Last updated:** 2026-07-08

---

## 1. One-line summary

Build an empirical, reproducible American football analytics platform that measures play,
player, unit, and coach value from EPA/WPA, predicts game outcomes and team strength,
values roster construction against the cap and NIL/revenue-sharing, and simulates
counterfactual coaching decisions — NFL first, then NCAA.

## 2. Motivation

Football sabermetrics is harder than baseball's isolated-event model: outcomes are
produced by 22 interacting players, coaches, scheme, and context, over small samples
(17 NFL / ~12 NCAA games). The public-data ecosystem is now strong enough (nflverse,
CollegeFootballData) to do serious play-level, player, tactical, roster-economics, and
finance modeling — provided the work is uncertainty-aware and license-compliant.

This vertical serves three roles that mirror the baseball flagship:

- **Coaching/decisions:** quantify what actually moves points and wins, and evaluate
  in-game decisions (fourth down, two-point, tempo, FG range) against an
  uncertainty-aware frontier.
- **Player/roster analysis:** value players by role against replacement, then against
  their cost (cap/cash/guarantees; NCAA compensation ranges).
- **Prediction & simulation:** forecast games and team strength, then run **AI Coach**
  counterfactual simulations and (later) health-cost labor-economics research.

## 3. Primary objective & sequencing

Priority order:

1. **NFL public-data warehouse + descriptive team analytics (PRIMARY).** nflverse
   play-by-play → EPA/WPA/success/explosive → opponent-adjusted team efficiency & style.
2. **Player performance models.** QB value, skill-position value, special teams,
   participation-based on/off, player-game opportunity.
3. **Team strength & game prediction.** Opponent-adjusted power ratings; win probability,
   margin, and total models benchmarked against the market; calibration reports.
4. **Player value & WAR-style + contract ROI.** Points-above-replacement → wins → cap/cash
   surplus; rookie-contract surplus; positional market efficiency.
5. **Tactical / coaching models → AI Coach simulation.** Decision models, then a policy
   engine that replays games under counterfactual decisions.
6. **NCAA:** CollegeFootballData ingestion → team PPA → finance → range-based compensation
   estimation.
7. **Research extensions:** injury/health-cost labor economics; NCAA-hockey (and general
   sport) compensation estimation; Big Data Bowl tracking-derived models.

Build the data foundation once; layer (1) → (7) on top of it. Full detail in
`docs/09-modeling-roadmap.md`.

## 4. Scope

**In scope (initial):**
- NFL regular season + postseason; nflverse play-by-play depth (1999+ PBP; participation/
  NGS aggregates 2016+).
- Team efficiency/style, player value by role, game prediction, contract/cap ROI, and
  fourth-down/decision analysis.
- NCAA (FBS-first) performance via CollegeFootballData; school-level finance; range-based
  compensation estimates — added after the NFL spine is proven.

**Out of scope (for now):**
- Full raw player tracking beyond public **Big Data Bowl** samples (raw NGS x/y is not
  public).
- Definitive OL/DL/LB/DB individual grades without charting/tracking (public estimates are
  proxies).
- Verified NCAA player-level compensation (does not exist publicly — estimate as ranges).
- Reselling or redistributing any raw proprietary/scraped feed (see compliance rules).
- Real-time in-game streaming / live-betting automation.

## 5. Success criteria

- **Reproducibility:** a season of NFL play-by-play metrics rebuilds from raw; EPA/WPA
  aggregations reconcile with public nflverse examples.
- **Prediction:** game win-probability model beats an Elo / market baseline on log-loss
  and is well-calibrated on held-out seasons; power ratings are opponent-adjusted.
- **Player value:** outputs carry replacement baselines, role/snap context, and
  uncertainty intervals; participation models are labeled as proxies, not grades.
- **Economics:** contract ROI uses cap/cash/guarantees/dead-money correctly; NCAA
  compensation is delivered as low/mid/high ranges with caveats.
- **Compliance:** every source used has documented license/ToS status, rate limits, and
  attribution (see `public-data-sources.md`).
- **Claim discipline:** every output labeled descriptive / predictive / causal /
  counterfactual / valuation.

## 6. Current phase

**Phase 0 → Phase 1 bootstrap.** The agent-context/documentation set is in place
(`PROJECT_CONTEXT.md`, `CLAUDE.md`, `AGENTS.md`, `COMPANY_CONTEXT.md`, `registry.md`,
`public-data-sources.md`, and the `docs/` domain suite), and the initial installable
repo skeleton exists (`src/`, `dbt/`, `tests/`, `.env.example`, `pyproject.toml`,
`Makefile`, `docker-compose.yml`, `uv.lock`). The first NFL raw snapshots for 2025
have been written under `data/bronze/nflverse_schedules/...` and
`data/bronze/nflverse_pbp/...` with attribution and extract metadata. The first core
tables (`dim_game`, `fact_play`, `fact_team_game`) are built for 2025 under `data/core/`
and validated with Pandera. The first `team_style_season` analytics mart and Streamlit
dashboard are in place. EPA/WPA reconciliation now writes
`data/quality/epa_wpa_reconciliation/...`; core analysis-play EPA/WPA aggregates reconcile
to raw nflverse with zero practical drift, while the public cumulative all-row nflverse
definition is tracked separately. Next phase = add richer dashboard filters/exports and
pull player/roster/participation/snap-count raw data when network approval is available.

## 7. Domain context

### What this vertical is about
American football value must be estimated from play state (down, distance, field position,
clock, score, possession) rather than isolated events. The central metric is **Expected
Points Added (EPA)**; **Win Probability Added (WPA)** captures leverage; **success rate**
and **explosive-play rate** capture consistency vs. big-play identity. College football
uses **PPA (Predicted Points Added)** as the EPA analogue. The audience spans football
media, analysts, agents, small programs, and hiring managers.

### Key terminology

| Term | Definition |
|---|---|
| EPA | Expected Points Added: `EP_after − EP_before` for a play; core play-value metric. |
| WPA | Win Probability Added: `WP_after − WP_before`; leverage/game-management value. |
| Success rate | Binary efficiency: ≥40% of yards-to-go on 1st down, ≥60% on 2nd, conversion on 3rd/4th. |
| Explosive play | Common thresholds: pass ≥15–20 yds, rush ≥10–12 yds. |
| CPOE | Completion % Over Expected: QB accuracy vs. throw difficulty. |
| PPA | Predicted Points Added: CFB (CollegeFootballData/cfbfastR) analogue to EPA. |
| Participation / snaps | Who was on the field per play (NGS era, 2016+); unlocks on/off and adjusted plus-minus. |
| RAPM (football) | Regularized adjusted plus-minus over on-field players; a lineup-impact proxy. |
| WAR (public football) | Wins Above Replacement via points-above-replacement → wins (see nflWAR). |
| Cap hit / cash / guarantees / dead money | Distinct contract-accounting views — they answer different questions. |
| NIL | Name/Image/Likeness compensation; a market/brand valuation, **not** verified salary. |
| Revenue sharing | Post–*House v. NCAA* direct school→athlete payments under an annual institutional cap (~$20.5M in 2025-26). |

### Key questions this project answers
1. How efficient is each team, adjusted for opponent and context, and what is its identity?
2. How much value does each player create by role, above replacement, with what uncertainty?
3. Which in-game decisions were right, and how does each coach's risk preference look?
4. Which contracts/roster constructions are efficient per cap and cash dollar?
5. How would an AI Coach's decisions have changed a team's season?
6. (NCAA) What is a player's economically implied compensation range under NIL/revenue-sharing?

## 8. Data sources (summary)

Full catalog with ToS/attribution in `public-data-sources.md`; access detail in
`docs/01`, `docs/03`, `docs/07`.

| Dataset | Source | Access | League | Status | Notes |
|---|---|---|---|---|---|
| Play-by-play + schedules | nflverse / nflfastR | R/Python loaders over release files | NFL | Planned | Central fact table; 1999+; snapshot versions. |
| Rosters / players / IDs | nflreadr / nfl_data_py | Loaders | NFL | Planned | Needs ID bridge (GSIS/PFR/ESPN). |
| Participation + snap counts | nflreadr | Loaders | NFL | Planned | 2016+; unlocks on/off, adjusted +/−. |
| NGS aggregates | nflreadr::load_nextgen_stats | Loaders | NFL | Planned | Aggregates only; raw tracking not public. |
| Injuries / depth charts | nflreadr | Loaders | NFL | Planned | Status/games-missed proxies only. |
| Contracts / cap | OverTheCap via load_contracts; NFLPA; Spotrac | Loaders / web | NFL | Planned | Snapshot by date; cap≠cash≠guarantees≠dead money. |
| Tracking samples | NFL Big Data Bowl (Kaggle) | Kaggle download | NFL | Planned | Competition rules; store raw unchanged. |
| Games/plays/PPA/recruiting/finance | CollegeFootballData | API (key) via cfbfastR/cfbd-python | NCAA | Planned | Rate-limited; opponent adjustment mandatory. |
| Athletic-dept finance | EADA / Knight-Newhouse / USA Today | Public DBs | NCAA | Planned | Reconcile accounting definitions. |
| Team valuations/revenue | Forbes | Web | NFL | Planned | Estimates, not audited. |
| Betting lines | nflverse schedules / odds sources | Loaders / web | Both | Planned | Benchmark/feature only; store source+timestamp. |

## 9. Tech stack for this vertical

- **Primary language:** Python (R via renv for `nflreadr` / `cfbfastR` only).
- **Key libraries:** nflverse (nflfastR/nflreadr/nfl_data_py/nflreadpy), cfbfastR /
  cfbd-python, Polars/pandas, DuckDB, dbt, scikit-learn/XGBoost/LightGBM/statsmodels,
  PyMC/bambi, Pandera, MLflow.
- **Warehouse/storage:** object store (MinIO/S3) for `raw`; Postgres/DuckDB for curated.
- **dbt:** yes — raw → staging → core → analytics/features/models/finance.
- **Orchestration:** Dagster or Prefect (cron+Make acceptable early).
- **Visualization:** Plotly/Streamlit dashboards; static charts for reports.
- **Special:** CFBD API key handling; shared throttle/backoff + cache; ID-bridge tables.

## 10. Repository structure (proposed)

```
football-sabermetrics/
├── README.md · CLAUDE.md · AGENTS.md · COMPANY_CONTEXT.md · PROJECT_CONTEXT.md
├── registry.md · public-data-sources.md
├── docs/                       # domain suite (01–11) — see README index
├── pyproject.toml · .env.example · Makefile · docker-compose.yml
├── src/
│   ├── ingestion/              # nfl_pbp.py, cfbd.py, contracts.py, _throttle.py
│   ├── compliance/attributions.py
│   ├── features/ · models/ · simulation/  # AI Coach policy + counterfactual sim
│   └── serving/                # dashboards, report builders
├── dbt/models/{staging,core,analytics,features,models,finance}/
├── orchestration/ · r/ · notebooks/ · tests/ · data/ (git-ignored)
```

## 11. Important decisions made

| Date | Area | Decision | Rationale | Revisit if |
|---|---|---|---|---|
| 2026-07-08 | Data spine | nflverse is the canonical NFL spine; CollegeFootballData for NCAA | Best public play-level ecosystems; reproducible; API/ID coverage | A licensed feed becomes affordable and necessary. |
| 2026-07-08 | Sequencing | NFL first, NCAA second | NFL public data is cleaner and higher-attention; proves the engine | NCAA opportunity becomes time-sensitive. |
| 2026-07-08 | Storage | Snapshot all public sources even when reloadable | EPA/contracts/IDs/injuries get revised; reproducibility + backtests | — |
| 2026-07-08 | NCAA comp | Estimate as low/mid/high ranges, never "salary" | No public verified player-level compensation | Audited player-level data becomes public post-House. |
| 2026-07-08 | Player value | OL/DL/LB/DB shown as participation proxies with intervals | Public data lacks assignment/charting | Tracking/charting data acquired. |

## 12. Open questions
1. How far back to model NFL? (Participation/NGS only 2016+; older seasons need proxies.)
2. Object store now (MinIO) or start Parquet+DuckDB and port later, as baseball does?
3. Points-per-win value: estimate empirically from team point differential / EPA strength.
4. QB-availability handling for pregame prediction (announced inactives, late scratches).
5. Which CFBD endpoints to prioritize for a first NCAA team-PPA model?

## 13. Known issues and gotchas
- Football player identity is unstable (team/position/number/name changes) — build the ID
  bridge early or joins will silently break.
- Raw NGS tracking is **not** public; only aggregates and Big Data Bowl samples are.
- Contract fields are not interchangeable; AAV alone is misleading.
- CFBD needs an API key and is rate-limited; cache aggressively.
- NCAA finance sources (EADA vs. MFRS/Knight vs. USA Today) use different definitions.
- Betting markets include margin/timing — store line source + timestamp; never treat as truth.

## 14. Current priorities (next, small and concrete)
1. Pull the next NFL raw sources now wired in `src.ingestion.nflverse`: teams, players,
   rosters, participation, and snap counts.
2. Expand the team efficiency/style dashboard with filters, exports, and clearer tempo /
   fourth-down placeholders.
3. Build `dim_team`, initial `dim_player`, and ID bridge tables from teams/players/rosters.
4. Keep test/lint gates green as ingestion expands (`pytest`, `ruff`).
5. Expand `src/compliance/attributions.py` stamping from raw/core/analytics/quality snapshots
   into exported reports.

## 15. Cross-vertical connections

| This vertical | Connects to | How |
|---|---|---|
| Adjusted plus-minus / on-field value | Basketball (RAPM), Soccer (VAEP/g+) | Same regularized player-effect design |
| WAR / replacement value | Baseball (WAR) | Points-to-wins + role baselines |
| AI Coach decision simulation | Board Game AI | Sequential decisions, MDP / offline policy eval |
| Contract & cap surplus | Game Analytics (economy), Economics | Value-per-cost, salary efficiency |
| Revenue & health-cost labor economics | Economics | Panel data, fixed effects, event studies, DiD |
| Recruiting / draft value | Baseball (prospect), Economics (human capital) | Survival + development curves |

## 16. Companion files
- Operating rules for agents: `CLAUDE.md`
- Tool-agnostic agent quick-start: `AGENTS.md`
- Sports vertical brief: `../CLAUDE.md`
- Company mission: `../../COMPANY_CONTEXT.md`, `COMPANY_CONTEXT.md`
- Code/tool inventory + licenses: `registry.md`
- Data catalog + ToS + attribution: `public-data-sources.md`
- Domain deep-dives: `docs/` (index in `README.md`)
- Build/run + layout: `README.md`

## 17. Next review date
Review after: the NFL `raw` + `fact_play` foundation is reproducible; a first team
dashboard ships; the storage-engine decision (§12.2) is settled; or scope changes.
