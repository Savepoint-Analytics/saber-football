# COMPANY_CONTEXT.md

Company: **Savepoint Analytics**
Project: **American Football Sabermetrics (NFL + NCAA)**
Owner/operator: **Alex Oswald**
Created: 2026-07-08

> Project-level business context. Inherits the global `../../COMPANY_CONTEXT.md`.
> Where they conflict, the global file governs business positioning; this file adds
> football-specific audiences, offers, and boundaries.

## Company purpose

Savepoint Analytics is an independent analytics consultancy focused on practical,
end-to-end analytical products: data engineering, statistical modeling, experimentation,
forecasting, machine learning, dashboarding, and domain expertise combined into
affordable, trustworthy analysis. The core business is game-studio analytics; the public
research portfolio (sports, elections, wildlife, economics, board-game AI) diversifies
beyond the volatile game industry and compounds domain knowledge across verticals.

This American football project extends the sports-sabermetrics vertical from baseball
into the two highest-attention football markets in North America — the NFL and NCAA
college football — while reusing the same reproducible, public-data-first engine.

## Why football fits Savepoint Analytics

American football sabermetrics sits at the intersection of:

- sequential decision-making under uncertainty (down/distance/clock/score);
- multi-agent value attribution (22 players, coaches, scheme);
- noisy, low-sample outcomes and process metrics (EPA, WPA, success rate);
- talent evaluation and replacement-level thinking;
- hard salary-cap economics, contract surplus, and (in NCAA) revenue-sharing/NIL;
- injury, health-cost, and labor economics;
- explainable, public-facing analysis.

These overlap strongly with Savepoint's existing strengths in game analytics, economy
balancing, experimentation, telemetry design, predictive modeling, simulation, and
decision support. The AI Coach simulation program in particular is a direct cousin of
board-game NPC decision policies and game-economy tuning.

## Business goals

### Near-term
- Build a credible public portfolio in football analytics (NFL first).
- Publish explainable, reproducible analysis from public data (nflverse, CollegeFootballData).
- Demonstrate the ability to ingest messy football data, conform it, model it with
  appropriate uncertainty, and communicate findings to non-technical audiences.
- Produce reusable artifacts: team efficiency/style dashboards, QB and skill-player value
  cards, fourth-down decision reports, and contract-surplus tables.

### Medium-term
- Offer affordable analysis packages to fans, media writers, fantasy/DFS-adjacent
  analysts (where legal), agents, and small/grassroots or college programs.
- Ship an **AI Coach** decision-simulation product (fourth-down/two-point/tempo policy
  vs. actual coaching) as a distinctive, defensible portfolio centerpiece.
- Build NCAA performance models plus range-based compensation estimates suited to the
  post–*House v. NCAA* revenue-sharing/NIL landscape.
- Use the work to pursue contract opportunities or employment in sports analytics, sports
  data vendors, teams, programs, or media.

### Long-term
- Be known for rigorous, accessible football analytics that respects the sport's
  interdependence and quantifies uncertainty honestly.
- Extend into football labor economics (injury risk vs. compensation vs. health-cost
  inflation) and the NCAA-hockey/other-sport compensation-estimation framework that
  reuses the same revenue-share allocation engine.
- Keep the pipeline sport-agnostic so the same platform serves baseball, basketball,
  soccer, tennis, and football.

## Positioning

> Affordable, rigorous American football analytics for people who want to understand the
> game empirically — play value, decisions, roster economics — without pretending public
> data grades every player or predicts the future with false precision.

Potential audiences:

- NFL and college football media, writers, and podcasters;
- fantasy/DFS-adjacent and betting-adjacent analysts, within legal and ethical bounds;
- player agents and player-development staff;
- small-college and grassroots programs needing affordable decision/roster analysis;
- data-science hiring managers and sports data vendors;
- fans who appreciate quantified, uncertainty-aware analysis.

## Differentiators

- Senior data engineering + analytics engineering + data science + strategy in one operator.
- Public, reproducible pipelines over inaccessible proprietary feeds — transparent enough
  for portfolio and open research.
- Games background (economy systems, telemetry, experimentation, simulation) maps cleanly
  onto play-value attribution, roster/cap balancing, and counterfactual coaching sim.
- Explains technical results to non-technical audiences; quantifies uncertainty instead
  of selling false certainty.
- License-compliant by default — a professional differentiator, not an afterthought.

## Service concepts

### Team efficiency & style reports
EPA/play, success rate, explosive rate, pass rate over expected, tempo, fourth-down
aggressiveness, red-zone efficiency, opponent-adjusted — plus a plain-language "who this
team is" summary.

### Player value cards
Role-adjusted QB / skill-position / unit profiles with EPA/WPA contribution, opportunity,
NGS-derived ability proxies, availability/injury context, replacement baseline, and
uncertainty. OL/DL/LB/DB shown as participation-based impact proxies, clearly labeled.

### Fourth-down & game-management decision reports
Go/kick/punt, two-point, and FG-range recommendations with confidence bands; coach
aggressiveness and risk-preference profiling against an uncertainty-aware frontier.

### Contract & cap surplus reports (NFL)
Cap-hit / cash / guaranteed / dead-money-adjusted ROI, rookie-contract surplus, positional
market efficiency, and roster-construction views.

### NCAA performance + compensation estimates
Team PPA, recruiting/returning-production/transfer context, and range-based (low/mid/high)
player compensation estimates under revenue-sharing/NIL, with explicit caveats.

### AI Coach simulation
Counterfactual play-calling and decision policy vs. actual coaching, with simulated
outcome distributions and season-level counterfactual win impact.

## Revenue paths

- Public reports and subscriptions.
- One-off team / player / matchup reports.
- Consulting packages for small programs, media, or agents.
- Data-pipeline builds for small organizations.
- Contract analytics work.
- Portfolio-driven employment opportunities.
- Sponsored analysis or media partnerships, with conflict-of-interest disclosures.

## Ethical and commercial boundaries

- Be transparent about public-data limitations; do not overstate model precision or imply
  raw player tracking / audited team financials the project does not have.
- Separate fan/media analysis from team-grade scouting claims.
- Never equate NIL valuations with actual compensation; use compensation ranges and
  separate scholarship / direct pay / NIL.
- Do not infer individual medical diagnoses from public injury data; keep health/labor
  work aggregate and non-sensational.
- Use gambling-adjacent analysis cautiously and legally; keep the primary focus on sport
  understanding, decisions, player development, and team/program performance.
- Respect every source license and rate limit; do not redistribute raw third-party data;
  attribute sources clearly in published work.

## Brand voice

Clear, empirical, practical, and humble. Avoid hot takes and false certainty. Football is
interdependent and low-sample; good analysis quantifies uncertainty and states its limits.

## Connection to games analytics

The same core skills transfer when adapted properly:

- telemetry ingestion → play-by-play / participation ingestion;
- player-behavior modeling → play-value and player-on-field attribution;
- economy balancing → salary-cap / roster / NIL efficiency;
- experiment design → quasi-experimental evaluation of tactics and decisions;
- retention/funnel analysis → player development, availability, and career-value modeling;
- simulation → game/season outcome and AI Coach counterfactual modeling.

## Company compliance stance

License compliance is treated as a professional differentiator. Every public deliverable
should carry source attribution, a description of limitations, and a note when analysis is
based on public or estimated data rather than official team/vendor data. See
`public-data-sources.md` and `CLAUDE.md` §5.
