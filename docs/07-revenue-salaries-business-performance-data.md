# Revenue, Salaries, and Business-Performance Data

Last updated: 2026-07-08

## Summary

A football sabermetrics project should connect on-field performance to economic value. For the NFL, the strongest public salary data comes from NFLPA, OverTheCap, Spotrac, and nflreadr contract loaders. For business performance, use Forbes estimates, attendance, stadium data, local market proxies, playoff appearances, media context, and team performance. For NCAA, use EADA, Knight-Newhouse, USA Today finances, school/conference reports, revenue-sharing policy information, and CollegeFootballData performance data.

## NFL salary and cap data

### NFLPA Public Salary Cap Report

- URL: https://nflpa.com/reports/public-salary-cap-report
- What it provides: official public cap report, generated daily.
- Important fields: current contracts, previous-year carryover, adjustments, team cap, active cap spending, dead money, effective cap room.
- Use case: official cap baseline and point-in-time cap state.
- Storage: snapshot by date.

### OverTheCap

- URL: https://overthecap.com/
- What it provides: player contracts, cap hits, cash, dead money, positional spending, cap calculators, contract structures, team salary cap tables.
- nflreadr bridge: `load_contracts()` loads historical player contracts from OverTheCap.
- Use case: roster construction, contract surplus, positional market values, dead-money analysis.
- Storage: contract-year table plus raw snapshot.

### Spotrac

- URL: https://www.spotrac.com/nfl/
- What it provides: contracts, guarantees, salary breakdowns, team payroll, salary cap tracker, transactions, positional rankings.
- Use case: cross-check contracts, guarantees, and cash flows.
- Storage: snapshot by date, especially for active contracts and cap tables.

### nflreadr contracts

Example:

```r
library(nflreadr)

contracts <- load_contracts()
```

Recommended normalized table:

```text
fact_contract_year
  season
  player_id
  team
  position
  cap_hit
  cash_paid
  base_salary
  signing_bonus_proration
  roster_bonus
  option_bonus
  workout_bonus
  incentives
  guaranteed_amount
  dead_money
  contract_start_year
  contract_end_year
  rookie_contract_flag
  source
  source_snapshot_date
```

## NFL business-performance data

### Forbes team valuations

- URL example: https://www.forbes.com/sites/justinteitelbaum/2025/08/28/the-nfls-most-valuable-teams-2025/
- What it provides: estimated team value, revenue, operating income, and valuation changes.
- Use case: long-run business performance, franchise value, and revenue models.
- Caveat: Forbes figures are estimates, not audited financial statements.

### Attendance and stadium data

Sources:

- Pro Football Reference;
- ESPN attendance summaries;
- official team/stadium reports;
- Wikipedia/stadium capacity cross-checks;
- public ticket market data if available.

Use cases:

- win/loss impact on attendance;
- stadium effect on revenue;
- market-size and fan-demand modeling;
- weather/roof/surface interactions.

### Media and market data

Potential sources:

- national TV schedule;
- primetime appearances;
- playoff appearances;
- Nielsen/media reports where available;
- Google Trends;
- social-media following;
- local market population/income;
- merchandise proxies.

Use cases:

- star-player and QB impact;
- revenue lift from contention;
- brand growth;
- demand elasticity.

## NCAA finance data

### EADA

- URL: https://ope.ed.gov/athletics/
- What it provides: equity in athletics participation, revenues, and expenses.
- Grain: institution, sport, reporting year.
- Use case: sport-level revenues/expenses and public disclosure baseline.
- Caveat: EADA accounting has known limitations and may not match NCAA MFRS reporting.

### Knight-Newhouse College Athletics Database

- URL: https://knightnewhousedata.org/
- About data: https://knightnewhousedata.org/about-the-data
- What it provides: public college athletics revenue and expense data drawn from public reports filed through NCAA Membership Financial Reporting System for covered Division I institutions.
- Use case: stronger public finance source for public DI athletic departments.
- Useful categories:
  - media rights;
  - conference and NCAA distributions;
  - post-season football;
  - sponsorship/licensing;
  - donor contributions;
  - ticket sales;
  - competition guarantees;
  - institutional/government support;
  - coaching compensation;
  - facilities;
  - recruiting;
  - student aid;
  - medical expenses where available.

### USA Today NCAA finances

- URL: https://sportsdata.usatoday.com/ncaa/finances
- What it provides: public revenue/expense rankings and school-level finance summaries.
- Use case: cross-checking public-school finance data and creating broad comparisons.

### School and conference reports

Sources:

- annual financial reports;
- athletic department reports;
- conference distributions;
- open records requests;
- audited financial statements for public institutions where available.

Use case:

- deeper finance modeling;
- validation of EADA/Knight totals;
- sport-specific expenses and revenue-sharing allocation.

## Revenue model targets

### NFL targets

- team revenue;
- operating income;
- franchise value;
- attendance;
- ticket revenue proxies;
- merchandise/social interest proxies;
- playoff revenue proxies;
- local fan demand;
- salary-cap efficiency;
- roster surplus value.

### NCAA targets

- athletic department revenue;
- sport-specific football revenue;
- donor contributions;
- sponsorship/licensing;
- ticket sales;
- media/conference distributions;
- post-season football revenue;
- institutional support;
- revenue-sharing pool allocation;
- compensation efficiency.

## Modeling framework: performance to revenue

### NFL team-year panel

```text
team_revenue_it =
  team_fixed_effect_i
+ year_fixed_effect_t
+ beta1 * wins_it
+ beta2 * playoff_appearance_it
+ beta3 * qb_star_value_it
+ beta4 * stadium_newness_it
+ beta5 * market_income_i
+ beta6 * primetime_games_it
+ beta7 * lagged_wins_i,t-1
+ error_it
```

Use fixed effects to separate stable franchise/market differences from performance changes.

### NCAA school-year panel

```text
football_revenue_it =
  school_fixed_effect_i
+ year_fixed_effect_t
+ conference_year_effect_ct
+ beta1 * wins_it
+ beta2 * playoff_or_bowl_it
+ beta3 * recruiting_rank_i,t-1
+ beta4 * home_attendance_it
+ beta5 * media_distribution_it
+ beta6 * donor_contributions_it
+ error_it
```

For NCAA, conference realignment and media-rights changes are major confounders.

## Salary/cap efficiency framework

### NFL

```text
team_salary_efficiency = wins_above_replacement / cap_spending
player_surplus = player_war * market_price_per_win - cap_hit
```

Variants:

- cap-hit ROI;
- cash ROI;
- guaranteed-money ROI;
- dead-money-adjusted ROI;
- rookie-contract surplus;
- free-agent surplus;
- positional spending ROI.

### NCAA

```text
estimated_compensation_efficiency = player_value / estimated_total_compensation
```

Use compensation ranges instead of exact values:

```text
low_estimate_surplus
mid_estimate_surplus
high_estimate_surplus
```

## Health and injury economics data

Sources:

- nflreadr injuries;
- NFL official injury reports;
- games missed;
- injured reserve transactions;
- snap exposure;
- player salary/cash/cap;
- workers' compensation reports where accessible;
- public medical cost inflation indices;
- CBA benefit structures;
- career length and post-career health studies.

Potential targets:

- salary paid while injured;
- career earnings lost to injury;
- injury risk by position and age;
- medical cost exposure over time;
- compensation premium for dangerous roles;
- adequacy of benefits relative to health-care inflation.

## Recommended marts

- `mart_nfl_contract_roi`
- `mart_nfl_positional_spending`
- `mart_nfl_roster_surplus`
- `mart_nfl_team_revenue_panel`
- `mart_nfl_team_value_panel`
- `mart_nfl_injury_cost_panel`
- `mart_ncaa_school_finance_panel`
- `mart_ncaa_football_revenue_panel`
- `mart_ncaa_compensation_estimates`
- `mart_ncaa_revenue_sharing_allocations`

## Main caveats

1. NFL team financials are private; public valuation/revenue data is estimated.
2. NFL contract accounting is complex; cap hit, cash, guarantee, and dead money answer different questions.
3. NCAA finance data varies by reporting system.
4. NCAA player-level compensation is incomplete and often estimated.
5. Revenue models require careful causal design because winning, revenue, market, stadium, media, and star players are jointly determined.
