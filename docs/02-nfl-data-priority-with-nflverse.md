# NFL Data Priority with nflverse

Last updated: 2026-07-08

## Recommendation

Use `nflverse` as the NFL data spine. It should be the first source loaded, the first source modeled, and the canonical ID layer for NFL football analytics.

The reason is straightforward: public NFL sabermetrics lives at the play level, and `nflverse` gives you the cleanest public path from play-by-play to EPA, WPA, schedules, rosters, participation, injuries, contracts, combine, draft, and player/team identifiers.

## Data priority order

### Priority 1 — Play-by-play and schedule foundation

Tables:

- `nfl_pbp`
- `nfl_schedules`
- `nfl_teams`

Why this comes first:

- Expected points and win probability are play-state models.
- Team performance must be evaluated by down, distance, field position, time, score, and opponent.
- Every downstream model starts from `game_id` and `play_id`.

Core metrics:

- EPA/play
- WPA/play
- success rate
- explosive-play rate
- turnover rate
- drive points
- scoring probability
- early-down EPA
- late-down conversion value
- neutral-script efficiency
- red-zone and backed-up efficiency

Example access:

```r
library(nflreadr)

pbp <- load_pbp(1999:2025)
schedules <- load_schedules(1999:2025)
```

```python
import nfl_data_py as nfl

pbp = nfl.import_pbp_data(range(1999, 2026))
schedules = nfl.import_schedules(range(1999, 2026))
```

### Priority 2 — Player identity, rosters, and positions

Tables:

- `nfl_players`
- `nfl_rosters`
- `nfl_player_ids`
- `nfl_depth_charts`

Why this matters:

- Football players change teams, positions, jersey numbers, and naming conventions.
- Player modeling breaks quickly without a stable ID bridge.
- Depth charts and rosters are needed to define replacement level and opportunity.

Modeling uses:

- position-specific baselines;
- roster age curves;
- draft-to-roster survival;
- role stability;
- replacement-player definitions;
- team construction analysis.

### Priority 3 — Participation and snap context

Tables:

- `nfl_participation`
- `nfl_snap_counts`

Why this is the public-data unlock:

Football player value cannot be estimated only from box scores. A player can affect a play without touching the ball. Participation data provides who was on the field, offensive/defensive personnel context, box counts, and other play-level context starting in the NGS era.

Use cases:

- on/off impact;
- player-on-play adjusted plus-minus;
- personnel package efficiency;
- defensive box-count adjustment;
- player interaction models;
- offensive line, defensive line, linebacker, and secondary value proxies;
- tactical tendency modeling.

Recommended model grain:

`game_id + play_id + player_id + team + offense_defense_side`

### Priority 4 — Player weekly/seasonal performance

Tables:

- `nfl_weekly_player_stats`
- `nfl_seasonal_player_stats`
- `nfl_team_stats`
- `nfl_nextgen_stats`

Why this matters:

- Weekly stats support player-game features, injury-return analysis, trend models, and fantasy-adjacent opportunity measures.
- NGS aggregates add public ability proxies that box scores miss.

Examples:

- QB CPOE, average time to throw, air yards, aggressiveness;
- receiver separation, YAC over expected, cushion;
- rushing efficiency, yards over expected, stacked-box rate;
- team EPA splits and situational performance.

### Priority 5 — Injuries, status, and availability

Tables:

- `nfl_injuries`
- `nfl_depth_charts`
- `nfl_snap_counts`
- injured reserve / transaction feeds if available

Why this matters:

- Player availability changes team strength.
- Injuries confound player and coaching evaluation.
- Injury costs are central to labor economics, health care, career-length, and salary-risk research.

Modeling uses:

- injury-adjusted team strength;
- player replacement impact;
- health-cost inflation study design;
- salary paid while unavailable;
- position-specific injury risk.

### Priority 6 — Contracts, cap, draft, and combine

Tables:

- `nfl_contracts`
- `nfl_salary_cap_snapshots`
- `nfl_draft_picks`
- `nfl_draft_pick_values`
- `nfl_combine`

Why this matters:

- Sabermetrics should connect performance to cost.
- Football has a hard salary cap and contract structures that create surplus, dead money, and roster constraints.

Modeling uses:

- wins above replacement per cap dollar;
- rookie contract surplus;
- free-agent overpay/underpay;
- draft pick expected value;
- contract-year aging curves;
- positional spending efficiency.

### Priority 7 — Market, weather, venue, and rest context

Tables:

- `nfl_betting_lines`
- `nfl_weather`
- `nfl_stadiums`
- `nfl_rest_travel`

Why this matters:

- Betting markets are strong priors for team strength.
- Weather, roof, surface, rest, travel, and time zone affect performance.
- Tactical evaluation needs to avoid confusing context with skill.

Modeling uses:

- pregame win probability;
- spread/margin prediction;
- market-adjusted surprise;
- weather-adjusted pass/rush/kick models;
- rest-adjusted injury and efficiency models.

## Canonical data model centered on nflverse

```text
dim_game
  game_id
  season
  week
  season_type
  home_team
  away_team
  venue
  roof
  surface
  weather
  spread_line
  total_line

fact_play
  game_id
  play_id
  posteam
  defteam
  down
  ydstogo
  yardline_100
  game_seconds_remaining
  score_differential
  play_type
  epa
  wp
  wpa
  success
  passer_player_id
  rusher_player_id
  receiver_player_id

fact_player_on_play
  game_id
  play_id
  player_id
  team
  side
  position
  role
  snap_participation_flag

fact_player_game
  game_id
  player_id
  team
  position
  snaps
  opportunities
  box_score_stats
  ngs_stats
  injury_status

fact_contract_year
  season
  player_id
  team
  cap_hit
  cash
  guarantees
  dead_money
  contract_status
```

## Why nflverse first instead of a paid API?

1. It is public and reproducible.
2. It has strong community validation.
3. It exposes play-by-play and EPA/WPA fields needed for football sabermetrics.
4. It integrates with R and Python.
5. It allows development before committing to expensive tracking/charting vendors.
6. It is transparent enough for open research and portfolio work.

## When to add paid data later

Add paid/proprietary data only after the public pipeline proves useful. The highest-value upgrades would be:

- full player tracking;
- route labels;
- coverage labels;
- pressure/blocking charting;
- offensive line assignment data;
- defensive responsibility data;
- practice participation and medical detail;
- verified real-time injuries;
- audited business financials.

## Initial build sequence

1. Load all nflverse play-by-play and schedules.
2. Build `dim_game`, `fact_play`, and `team_game_efficiency`.
3. Add rosters and player IDs.
4. Add participation and snap counts.
5. Add weekly player stats and NGS aggregates.
6. Add injuries and depth charts.
7. Add contracts, cap, draft, and combine.
8. Add betting lines and weather.
9. Build player-value, team-style, and roster-efficiency marts.
10. Only then add Big Data Bowl tracking samples and specialized tracking-derived models.
