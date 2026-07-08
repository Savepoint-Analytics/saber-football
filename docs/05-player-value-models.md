# Player-Value Models for American Football

Last updated: 2026-07-08

## Summary

Football player value is difficult because production is interdependent. A QB's EPA depends on receivers, pass protection, play design, defense, field position, and game state. A guard, edge rusher, safety, or blocking tight end may materially affect the play without receiving a clean public stat. The public-data approach should therefore combine play-level value, participation, position-specific opportunity, replacement baselines, and salary/roster context.

## Target question

> How much does a player improve a team's ability to win, after adjusting for context, teammates, opponents, tactics, injuries, and roster cost?

## Model family overview

| Model | Best use | Strength | Weakness |
|---|---|---|---|
| EPA contribution | Skill players, team units, play types | Simple and interpretable | Can over-credit players who touch the ball |
| WPA contribution | High-leverage game impact | Directly tied to wins | Highly context-dependent and noisy |
| WAR / wins above replacement | Cross-player value on win scale | Aligns with roster decision-making | Replacement baseline is hard in football |
| Adjusted plus-minus / RAPM | Player-on-field value | Captures hidden player impact | Needs participation data and shrinkage |
| Hierarchical Bayesian player model | Position-aware value with uncertainty | Handles small samples and partial pooling | More complex to build and explain |
| Tracking-derived value | Spatial value, routes, tackling, coverage | Best for hidden football actions | Raw full-season tracking is not public |
| Contract ROI / surplus value | Performance per salary/cap dollar | Links analytics to roster economics | Contract accounting is complicated |

## Core player-value tables

### fact_player_game

Player-game box and opportunity stats.

Important fields:

- `season`
- `week`
- `game_id`
- `player_id`
- `team`
- `opponent`
- `position`
- `snaps_offense`
- `snaps_defense`
- `snaps_special_teams`
- passing/rushing/receiving/defensive/special-teams stats
- NGS aggregates
- injury status
- depth chart status

### fact_player_on_play

Player participation at play grain.

Important fields:

- `game_id`
- `play_id`
- `player_id`
- `team`
- `side`
- `position`
- `personnel_group`
- `box_count`
- `pass_rushers`
- `epa`
- `wpa`
- `play_type`

This is the bridge from box-score player analytics to football-specific on-field value.

### fact_contract_year

Player cost at season/team grain.

Important fields:

- `season`
- `player_id`
- `team`
- `cap_hit`
- `cash_paid`
- `base_salary`
- `signing_bonus_proration`
- `guaranteed_money`
- `dead_money_if_cut`
- `contract_year_number`
- `rookie_contract_flag`
- `franchise_tag_flag`

## EPA-based contribution model

Basic model:

```text
player_epa = sum(EPA on plays where player is primary actor)
```

Better model:

```text
adjusted_player_epa = f(
  play EPA,
  role/opportunity,
  down_distance,
  field_position,
  score_state,
  opponent_strength,
  teammates,
  personnel,
  game environment,
  player position
)
```

Use for:

- QB dropbacks;
- rusher attempts;
- receiver targets;
- returners;
- kickers;
- punters.

Limitations:

- primary actor framing over-credits players with the ball;
- routes without targets are mostly invisible;
- blocking and coverage remain undermeasured;
- play-call selection creates bias.

## QB value model

Suggested components:

- dropback EPA;
- CPOE;
- sack rate over expected;
- interception rate over expected;
- air-yards profile;
- scramble value;
- third/fourth-down performance;
- red-zone performance;
- pressure sensitivity;
- play-action/screen split;
- opponent-adjusted efficiency;
- receiver/separation context;
- pass-blocking context where available;
- garbage-time filtering.

Target outputs:

- QB EPA above replacement;
- QB wins above replacement;
- QB contract surplus;
- QB tactical fit score;
- QB health/availability risk.

## Receiver value model

Suggested components:

- targets per route if available;
- target share;
- air-yard share;
- yards per route run if route data available;
- EPA per target;
- first downs per target;
- explosive rate;
- YAC over expected;
- separation from NGS aggregates;
- contested-catch proxies;
- drop proxies;
- route distribution where available;
- QB adjustment;
- coverage/opponent adjustment.

Public-data issue: route participation is not fully public. Snap counts and targets help, but complete route-run data often requires paid charting or tracking.

## Running back value model

Suggested components:

- rush EPA;
- success rate;
- rushing yards over expected where available;
- stacked-box rate;
- runs by box count;
- short-yardage success;
- receiving EPA;
- pass-protection proxy if available;
- explosive rate;
- fumble risk;
- workload/injury risk;
- contract cost.

Caution: rushing production is highly dependent on line, scheme, box count, and game script.

## Offensive line value model

Public-data approach:

- player-on-field adjusted EPA;
- team pressure/sack rate by OL combination if pressure data available;
- rushing success by side/gap if available;
- penalties;
- snap availability;
- QB time-to-throw and sack context;
- injury replacement effects;
- pass/run split by lineup.

Best public model:

```text
play_epa ~ offensive_line_players + qb + skill_players + defense + down_distance + field_position + game_state + team + opponent + season
```

Use strong regularization and position priors. Without blocking assignment data, OL estimates should be presented as lineup-impact proxies, not definitive individual grades.

## Defensive player value model

Public-data approach by role:

### Defensive line / edge

- pressure proxy if available;
- sacks and QB hits;
- tackles for loss;
- defensive EPA when on field;
- run defense by box/personnel;
- opponent pass rate and game script;
- pass-rush group combinations.

### Linebacker

- tackle involvement;
- box count context;
- coverage target outcomes where available;
- run fit proxies;
- blitz/pass-rush role;
- on-field EPA allowed.

### Defensive backs

- targets allowed if charted;
- coverage classification if available;
- explosive passes allowed by personnel/side if available;
- interceptions/pass breakups;
- on-field pass EPA allowed;
- safety/slot/outside role context.

Caution: public defensive attribution is weaker than offensive attribution without charting or tracking.

## Special teams value model

Components:

- field goal EPA/WPA;
- kickoff EPA;
- punt EPA;
- return EPA;
- field position added;
- hang time and placement if available;
- opponent-adjusted return prevention;
- weather and stadium adjustment;
- leverage adjustment.

Special teams can be valued cleanly because game state before/after special-teams plays is well-defined.

## WAR-style framework

High-level steps:

1. Estimate player contribution in EPA/WPA or points above average.
2. Define replacement level by position and role.
3. Convert points to wins.
4. Add uncertainty intervals.
5. Convert wins to salary/cap surplus.

Example:

```text
player_points_above_replacement = player_adjusted_points - replacement_points_for_role
player_war = player_points_above_replacement / points_per_win
contract_surplus = player_war * market_value_per_win - cap_hit_or_cash
```

Points-per-win can be estimated empirically by regressing wins or win percentage on point differential or EPA-derived team strength.

## Adjusted plus-minus / RAPM framework

Play-level outcome:

```text
EPA on play, success, first down, explosive allowed, pressure, turnover, or WPA
```

Design matrix:

- offensive players on field;
- defensive players on field;
- team;
- opponent;
- down/distance/yardline/time/score;
- personnel;
- play type;
- season/week;
- home/away/weather.

Model:

```text
EPA_play = context + offense_player_effects - defense_player_effects + error
```

Use:

- ridge regression;
- lasso/elastic net;
- hierarchical Bayesian model;
- partial pooling by position and role.

Output:

- player effect per snap;
- player effect per 100 snaps;
- total season effect;
- uncertainty interval;
- salary/cap surplus.

## Contract ROI model

Inputs:

- player WAR or points above replacement;
- cap hit;
- cash paid;
- guarantees;
- dead money;
- games missed;
- age;
- position;
- contract year;
- team contention window.

Outputs:

- cap dollars per WAR;
- cash dollars per WAR;
- surplus value;
- dead-money-adjusted surplus;
- rookie contract surplus;
- veteran contract risk;
- position market efficiency.

## Draft and development model

Targets:

- makes roster;
- plays NFL snap;
- starts games;
- reaches second contract;
- produces positive WAR;
- produces surplus value;
- longevity;
- injury-adjusted career value.

Features:

- draft round/pick;
- age;
- college production/PPA;
- recruiting rank;
- position;
- combine metrics;
- size/athletic traits;
- conference strength;
- team development environment;
- opportunity path.

Important caveat: combine metrics should not be treated as sufficient predictors of long-term success. Research suggests they can predict matriculation better than later performance.

## Reporting principles

Every player-value estimate should report:

- estimate;
- uncertainty interval;
- position-specific rank;
- role/snap context;
- team/opponent adjustment;
- cost/salary context;
- replacement baseline;
- data limitations;
- whether estimate is descriptive, predictive, or causal.

## Minimum viable public player-value product

1. QB value dashboard.
2. Skill-player opportunity and EPA dashboard.
3. Team unit EPA dashboard.
4. Participation-based on/off dashboard.
5. Contract surplus dashboard.
6. Rookie-contract surplus dashboard.
7. Injury-adjusted availability dashboard.
8. WAR-style experimental model with uncertainty.
