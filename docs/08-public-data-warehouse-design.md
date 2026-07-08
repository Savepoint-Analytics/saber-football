# Recommended Public-Data Warehouse Design

Last updated: 2026-07-08

## Summary

The warehouse should support play-level football analysis, player valuation, team-style analysis, roster/cap economics, NCAA finance, and counterfactual simulation. The key grain is play-by-play, but the warehouse must also handle player-on-play participation, player-game stats, team-game outcomes, contract years, school finance years, and model outputs.

## Design principles

1. Store raw data exactly as extracted.
2. Build cleaned/conformed tables separately.
3. Use stable IDs and explicit ID bridges.
4. Partition large tables by season and league.
5. Track source, extraction date, package version, and transformation version.
6. Keep model features and model outputs separate from raw/clean data.
7. Build point-in-time snapshots for changing data such as injuries, contracts, depth charts, betting lines, and salary caps.

## Suggested schemas

```text
raw
staging
core
analytics
features
models
finance
metadata
```

## Raw layer

Purpose: immutable source extracts.

Tables/files:

```text
raw.nfl_pbp_{season}
raw.nfl_schedules_{season}
raw.nfl_rosters_{season}
raw.nfl_players_snapshot_{date}
raw.nfl_participation_{season}
raw.nfl_snap_counts_{season}
raw.nfl_weekly_player_stats_{season}
raw.nfl_injuries_{season}
raw.nfl_depth_charts_{season}
raw.nfl_contracts_snapshot_{date}
raw.nfl_salary_cap_snapshot_{date}
raw.nfl_nextgen_passing_{season}
raw.nfl_nextgen_receiving_{season}
raw.nfl_nextgen_rushing_{season}
raw.nfl_big_data_bowl_{competition}_{file}
raw.cfb_games_{season}
raw.cfb_pbp_{season}
raw.cfb_drives_{season}
raw.cfb_player_stats_{season}
raw.cfb_team_stats_{season}
raw.cfb_ppa_{season}
raw.cfb_recruiting_{year}
raw.cfb_betting_{season}
raw.eada_{fiscal_year}
raw.knight_newhouse_{fiscal_year}
raw.usa_today_ncaa_finance_{fiscal_year}
```

## Staging layer

Purpose: normalize column names, types, and source quirks.

Examples:

```text
staging.stg_nfl_pbp
staging.stg_nfl_schedules
staging.stg_nfl_players
staging.stg_nfl_participation
staging.stg_nfl_contracts
staging.stg_cfb_pbp
staging.stg_cfb_games
staging.stg_cfb_recruiting
staging.stg_school_finance
```

Rules:

- one row per source record;
- preserve source IDs;
- cast numeric fields;
- standardize team aliases;
- keep source date/version columns;
- do not create derived modeling features yet unless they are source-defined.

## Core dimensions

### dim_league

```text
league_id
league_name
level
country
```

Values:

- `NFL`
- `NCAA_FBS`
- `NCAA_FCS`
- optional future: CFL, UFL, NCAA hockey.

### dim_team

```text
team_id
league_id
team_name
team_abbr
city
state
conference
division
active_from
active_to
source_team_ids
```

### dim_game

```text
game_id
league_id
season
week
season_type
home_team_id
away_team_id
game_date
kickoff_time
venue_id
neutral_site_flag
roof
surface
weather_summary
home_score
away_score
spread_close
total_close
```

### dim_player

```text
player_id
league_id
full_name
birth_date
height
weight
primary_position
college
high_school
source_ids_json
```

### dim_venue

```text
venue_id
venue_name
city
state
country
capacity
surface
roof_type
elevation
home_team_id
```

### dim_school

```text
school_id
school_name
state
conference
subdivision
public_private
carnegie_classification
```

## Core facts

### fact_play

Grain: one row per play.

```text
game_id
play_id
league_id
season
week
posteam_id
defteam_id
down
ydstogo
yardline_100
half_seconds_remaining
game_seconds_remaining
score_differential
play_type
pass_flag
rush_flag
special_teams_flag
passer_player_id
rusher_player_id
receiver_player_id
epa
wp_before
wp_after
wpa
success_flag
yards_gained
touchdown_flag
turnover_flag
penalty_flag
```

### fact_player_on_play

Grain: one player on one play.

```text
game_id
play_id
player_id
team_id
opponent_team_id
side
position
role
snap_flag
personnel_group
defenders_in_box
pass_rushers
source
```

### fact_team_game

Grain: one team in one game.

```text
game_id
team_id
opponent_team_id
home_away
points_for
points_against
win_flag
total_epa
offensive_epa
defensive_epa_allowed
special_teams_epa
success_rate
explosive_rate
turnover_margin
plays
pace_seconds_per_play
pass_rate_over_expected
fourth_down_aggressiveness
```

### fact_player_game

Grain: one player in one game.

```text
game_id
player_id
team_id
position
active_flag
starter_flag
injury_status
snaps_offense
snaps_defense
snaps_special_teams
passing_stats_json
rushing_stats_json
receiving_stats_json
defensive_stats_json
special_teams_stats_json
ngs_stats_json
```

### fact_contract_year

Grain: player-team-season contract/accounting record.

```text
season
player_id
team_id
position
cap_hit
cash_paid
base_salary
bonus_proration
guaranteed_remaining
dead_money
contract_start_year
contract_end_year
contract_status
source_snapshot_date
```

### fact_school_finance_year

Grain: institution-fiscal year.

```text
school_id
fiscal_year
source
total_athletic_revenue
total_athletic_expense
football_revenue
football_expense
ticket_sales
media_rights
conference_distributions
donor_contributions
sponsorship_licensing
student_fees
institutional_support
coaching_compensation
student_aid
medical_expenses
facilities_expenses
```

## Analytics marts

### Team style marts

```text
analytics.team_style_season
analytics.team_style_game
analytics.team_personnel_tendencies
analytics.team_fourth_down_decisions
analytics.team_pass_rate_over_expected
analytics.team_tempo
analytics.team_defensive_tendencies
```

### Player value marts

```text
analytics.player_epa_game
analytics.player_epa_season
analytics.player_on_off_impact
analytics.player_war_public
analytics.player_replacement_baselines
analytics.player_contract_roi
analytics.player_injury_availability
```

### NCAA-specific marts

```text
analytics.cfb_team_ppa
analytics.cfb_recruiting_talent
analytics.cfb_returning_production
analytics.cfb_transfer_impact
analytics.cfb_school_finance_panel
analytics.cfb_compensation_estimates
```

### Business marts

```text
finance.nfl_team_revenue_panel
finance.nfl_team_valuation_panel
finance.nfl_salary_cap_panel
finance.nfl_roster_surplus_panel
finance.ncaa_school_revenue_panel
finance.ncaa_sport_revenue_panel
finance.health_cost_inflation_panel
```

## Feature layer

Feature tables should be frozen inputs to models.

Examples:

```text
features.game_prediction_features
features.play_call_policy_features
features.fourth_down_decision_features
features.player_value_features
features.contract_roi_features
features.injury_risk_features
features.revenue_model_features
features.ai_coach_simulation_states
```

Each feature table should include:

- feature generation date;
- source data version;
- training/validation/test split flag;
- leakage warning if feature is not point-in-time safe;
- feature definitions.

## Model output layer

Examples:

```text
models.team_power_ratings
models.player_war_estimates
models.player_plus_minus_estimates
models.fourth_down_recommendations
models.play_call_policy_values
models.ai_coach_counterfactual_games
models.contract_surplus_estimates
models.revenue_impact_estimates
models.health_cost_exposure_estimates
models.ncaa_compensation_estimates
```

Each model output table should include:

- `model_run_id`;
- model name;
- model version;
- training window;
- prediction timestamp;
- estimate;
- lower interval;
- upper interval;
- calibration metrics;
- source data version.

## Metadata layer

Tables:

```text
metadata.source_extract_log
metadata.source_data_dictionary
metadata.id_resolution_log
metadata.model_run_log
metadata.feature_definition_registry
metadata.data_quality_checks
metadata.known_source_limitations
```

## ID resolution

Football data has many IDs. Maintain explicit bridges:

```text
bridge_player_ids
  canonical_player_id
  nflverse_id
  gsis_id
  pfr_id
  espn_id
  sportradar_id
  cfbd_id
  sports_reference_cfb_id
  recruiting_id
  name
  birth_date
  college
  confidence_score
```

```text
bridge_team_ids
  canonical_team_id
  league_id
  nfl_abbr
  cfbd_school
  sports_reference_team
  espn_team_id
  conference
  active_from
  active_to
```

## Technology options

### Local / prototype

- Parquet files;
- DuckDB;
- Python Polars/Pandas;
- R tidyverse/arrow;
- dbt-duckdb.

### Scalable open stack

- object storage: S3/MinIO;
- warehouse: Postgres, DuckDB, Snowflake, BigQuery, Redshift, or Athena/Iceberg;
- orchestration: Prefect;
- transformation: dbt;
- validation: Great Expectations or dbt tests;
- model tracking: MLflow.

## Recommended MVP build

1. Raw NFL play-by-play and schedules.
2. Core `dim_game`, `fact_play`, and `fact_team_game`.
3. Team efficiency and style marts.
4. Player weekly stats and rosters.
5. Player EPA and QB value marts.
6. Participation and snap-count tables.
7. Contracts and cap tables.
8. Player contract ROI.
9. NCAA CFBD play-by-play and finance tables.
10. AI Coach simulation feature states.
