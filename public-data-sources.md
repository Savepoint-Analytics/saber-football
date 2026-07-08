# public-data-sources.md — Football Data Catalog & Licensing (NFL + NCAA)

> The reusable "inventory of already-understood data" for the football vertical, framed
> around **licensing, ToS, rate limits, and required attribution.** For access patterns,
> tables, and code examples, see `docs/01` (NFL), `docs/03` (NCAA), and `docs/07`
> (revenue/salaries). Agents must check this file before pulling from any source.
> **Last updated:** 2026-07-08

---

## 0. The core distinction (read first)

A permissive **code** license (MIT on nflverse packages) does **not** grant rights to the
**data** those packages retrieve. Each upstream site/dataset has its own terms. Savepoint's
commercial/public posture:

> **Publish or sell derived analysis, models, and visualizations. Never resell or
> redistribute a source's raw data or bulk-scraped tables. Always attach required
> attributions, rate-limit, and cache.**

---

## 1. NFL source catalog

### nflverse (nflfastR / nflreadr / nfl_data_py / nflreadpy) — the NFL spine
- **Provides:** play-by-play with EPA/WP/CP/CPOE, schedules, rosters, player IDs,
  participation, snap counts, weekly/seasonal stats, NGS aggregates, injuries, depth
  charts, contracts, combine, draft.
- **Access:** R/Python package loaders over public `nflverse-data` release files
  (CSV/Parquet/RDS/QS).
- **License/ToS:** open-source community project (packages MIT). Data is aggregated from
  public sources for community use.
- **Commercial/public:** ✅ use freely for **derived analysis**. Attribute nflverse.
  Store versioned snapshots; do **not** re-publish the full raw release files as your own
  dataset. Pin package versions.
- **Attribution:** "Data via nflverse (nflfastR/nflreadr)."

### NFL Next Gen Stats (NGS)
- **Provides:** public **aggregate** passing/rushing/receiving metrics (CPOE, time to
  throw, separation, YAC over expected, etc.).
- **Access:** public site; nflverse NGS mirrors; `nflreadr::load_nextgen_stats()` (weekly
  player aggregates since 2016).
- **License/ToS:** NFL/NGS content. The **full raw x/y tracking feed is not public** —
  only aggregates/visualizations are.
- **Commercial/public:** ⚠️ aggregates via nflverse for derived analysis; do not imply you
  have raw tracking. Credit NFL / Next Gen Stats.

### NFL Big Data Bowl (player-tracking samples)
- **Provides:** player-tracking samples and challenge-specific labels (pre-snap tendencies,
  pass movement, special teams, tackling, etc.).
- **Access:** Kaggle competition downloads.
- **License/ToS:** governed by each **competition's rules**, which you must accept to
  download.
- **Commercial/public:** ⚠️ research/portfolio use per competition rules; **store raw files
  unchanged**; check the specific competition's terms before any commercial use.

### Pro Football Reference (Sports Reference family)
- **Provides:** historical player/team stats, game logs, standings, awards, attendance.
- **Access:** web tables; paid **Stathead** for deeper querying.
- **License/ToS:** bots/scrapers that impact the site are restricted; **rate limit ~20
  requests/min** (≤ 10 for Stathead); no products built on bulk-scraped data; no AI
  training on scraped data; attribute Sports Reference LLC.
- **Commercial/public:** ⚠️ conditional — light, attributed, page-level use only. Prefer
  nflverse for systematic pulls; use PFR for validation and older seasons.
- **Attribution:** "Stats courtesy of Pro-Football-Reference.com (Sports Reference LLC)."

### OverTheCap
- **Provides:** contracts, cap hits, cash spending, dead money, positional spending, cap
  space, restructures.
- **Access:** public web pages; `nflreadr::load_contracts()` loads OverTheCap-sourced
  historical contracts.
- **Commercial/public:** ⚠️ use `load_contracts()` for historical contracts; **snapshot by
  date** (data is revised after restructures/designations); do not redistribute their full
  contract database as a product. Attribute OverTheCap.

### Spotrac
- **Provides:** real-time contracts, guarantees, salary breakdowns, cap tables, payroll,
  transactions, rankings.
- **Access:** public pages; paid products.
- **Commercial/public:** ⚠️ snapshot when used; cross-check contracts/cap; do not
  redistribute raw tables. Attribute Spotrac.

### NFLPA Public Salary Cap Report
- **Provides:** official public cap report (generated daily): team cap, top-51, carryover,
  adjustments, dead money, effective cap room, active spending.
- **Access:** public web report.
- **Commercial/public:** ✅ public; **snapshot by date** if modeling cap state over time.
  Credit NFLPA.

### Forbes NFL team valuations
- **Provides:** estimated team value, revenue, operating income.
- **Access:** public articles.
- **Commercial/public:** ✅ cite as **estimates** (not audited financials). Credit Forbes.

### Betting lines / market data
- **Provides:** spread, total, moneyline, market-implied team strength.
- **Access:** nflverse schedules; sportsbooks; odds APIs; historical line datasets (check
  each provider's terms).
- **Commercial/public:** ⚠️ store open/close/source/timestamp; use as a **benchmark/
  feature, never ground truth**; keep gambling-adjacent framing cautious and legal.

### Weather / stadium
- **Provides:** roof, surface, temperature, wind, precipitation, stadium, altitude.
- **Access:** nflverse schedule fields; stadium metadata; public weather APIs (per their terms).
- **Commercial/public:** ✅ store schedule weather fields + external snapshots by game/timestamp.

## 2. NCAA / college football source catalog

### CollegeFootballData.com (cfbfastR / cfbd-python) — the NCAA spine
- **Provides:** games, teams, drives, plays, PPA, win probability, ratings, rankings,
  recruiting, transfer portal, player/team stats, advanced box scores, betting, venues,
  weather.
- **Access:** **API key required**; via `cfbfastR` (R) or `cfbd-python` (Python).
- **License/ToS:** CFBD's own terms; free/patron tiers with **rate limits**. Attribute
  CollegeFootballData.
- **Commercial/public:** ⚠️ respect terms, tiering, and rate limits; **cache** responses;
  store raw + cleaned tables; do not hammer the API for data already snapshotted.
- **Attribution:** "Data via CollegeFootballData.com."

### Sports Reference — College Football
- **Provides:** historical CFB teams, players, schedules, standings, bowls, awards.
- **Access:** web tables; Stathead.
- **License/ToS:** same Sports Reference constraints as PFR (rate limits; no bulk-scrape
  products; no AI training on scraped data; attribute SRL).
- **Commercial/public:** ⚠️ conditional; validation/enrichment only.

### Recruiting & transfer data
- **Provides:** prospect ratings, class rank, position, commitments, transfer history.
- **Access:** CFBD recruiting/transfer endpoints; public recruiting summaries.
- **Commercial/public:** ⚠️ store source, rating scale, recruit year, and match confidence;
  treat rankings as a **prior**, not a value measure.

### EADA (Equity in Athletics Disclosure Act)
- **Provides:** institution-submitted athletics participation, revenues, expenses.
- **Access:** public data tool / downloads (ope.ed.gov/athletics).
- **Commercial/public:** ✅ public; version by fiscal year; **accounting definitions are
  broad** and may not match NCAA MFRS.

### Knight-Newhouse College Athletics Database
- **Provides:** public DI athletics revenue/expense data from public MFRS reports (media
  rights, distributions, donor, ticketing, coaching comp, facilities, medical, etc.).
- **Access:** public database (knightnewhousedata.org).
- **Commercial/public:** ✅ strongest public finance source for covered public DI schools;
  version by fiscal year.

### USA Today NCAA finances
- **Provides:** ranked school revenue/expense data.
- **Access:** public database.
- **Commercial/public:** ✅ cross-check source; **reconcile definitions** with EADA/Knight.

### NCAA player compensation (NIL / revenue sharing) — ❗ not cleanly public
- **Provides:** no complete, audited, public player-level compensation table exists.
- **Context:** post–*House v. NCAA*: schools may directly share revenue (2025-26 cap
  ≈ $20.5M/institution); athletes may earn third-party NIL; deals above a threshold may be
  reviewed.
- **Commercial/public:** ❗ **estimation only.** Deliver low/mid/high **ranges**; separate
  scholarship / direct pay / NIL; never call NIL valuations "salary." State Title IX / legal
  uncertainty. (See `docs/06-ncaa-compensation-caveat.md`.)

## 3. Commercial/public-use cheat sheet

| Source | Use OK? | Attribution | Notes |
|---|---|---|---|
| nflverse (nflfastR/nflreadr/…) | ✅ derived analysis | ✅ nflverse | Don't republish raw releases; pin versions; snapshot. |
| NFL Next Gen Stats | ⚠️ aggregates only | ✅ NFL/NGS | Raw tracking not public. |
| NFL Big Data Bowl | ⚠️ per competition rules | ✅ per rules | Store raw unchanged. |
| Pro Football Reference / SR-CFB | ⚠️ conditional | ✅ SRL | ≤20 req/min; no bulk-scrape products; page-level only. |
| OverTheCap | ⚠️ via load_contracts; snapshot | ✅ OverTheCap | Don't redistribute full DB. |
| Spotrac | ⚠️ snapshot; cross-check | ✅ Spotrac | Don't redistribute raw tables. |
| NFLPA cap report | ✅ public | ✅ NFLPA | Snapshot by date. |
| Forbes valuations | ✅ as estimates | ✅ Forbes | Not audited. |
| Betting lines | ⚠️ benchmark/feature | per provider | Store source+timestamp; not ground truth. |
| CollegeFootballData | ⚠️ API key + rate limits | ✅ CFBD | Cache; store raw+clean. |
| EADA / Knight-Newhouse / USA Today | ✅ public | ✅ each | Reconcile accounting definitions. |
| NCAA player compensation | ❗ estimate as ranges | — | No verified public player-level data. |

**Default safe stack for a publishable/sellable product:** nflverse (derived NFL analysis)
+ CollegeFootballData (NCAA, keyed + cached) + public finance DBs (EADA/Knight/USA Today)
+ NFLPA cap report — all with attributions attached, contracts/cap/injuries snapshotted by
date, and NCAA compensation delivered as ranges.

## 4. When to add paid/licensed data later

Only after the public pipeline proves useful. Highest-value upgrades (see
`docs/02` §"When to add paid data later"): full player tracking, route/coverage labels,
pressure/blocking charting, OL assignment data, verified injuries, and audited business
financials — via licensed providers (e.g. Sportradar, Stats Perform, PFF, SIS), budget
permitting. These remove ToS ambiguity for products that distribute underlying data.

## 5. Attribution strings (stamp onto published outputs that use each source)

> "Data via nflverse (nflfastR / nflreadr)." ·
> "Includes NFL Next Gen Stats aggregates (via nflverse)." ·
> "College data via CollegeFootballData.com." ·
> "Contract data via OverTheCap / Spotrac." ·
> "Cap data via the NFLPA Public Salary Cap Report." ·
> "Stats courtesy of Pro-Football-Reference.com (Sports Reference LLC)." ·
> "NFL team financials are Forbes estimates, not audited figures." ·
> "NCAA finance via EADA / Knight-Newhouse / USA Today; NCAA player compensation figures
> are estimates, not verified salaries."

Centralize these in `src/compliance/attributions.py` and auto-stamp exports (see
`CLAUDE.md` §5).
