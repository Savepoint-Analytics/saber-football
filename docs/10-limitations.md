# Limitations and Caveats

Last updated: 2026-07-08

## Summary

American football analytics is powerful but constrained. Public data can support serious play-by-play, team, player, salary, and revenue modeling, but it cannot fully observe play design, assignments, routes, blocking, coverage responsibility, medical condition, true player compensation, or audited team finances. Every model should separate descriptive, predictive, and causal claims.

## Football-specific limitations

### 1. Football is highly interdependent

A play outcome is produced by 22 players, coaches, play design, communication, field position, game state, weather, officiating, and random variation.

Implication:

- do not over-credit the player who touches the ball;
- use teammate/opponent controls;
- report uncertainty;
- build role-specific models.

### 2. Sample sizes are small

NFL teams play 17 regular-season games. College football teams play about 12 regular-season games. Player-level samples can be tiny, especially for linemen, defensive backs, backups, and situational players.

Implication:

- use shrinkage and hierarchical models;
- avoid overreacting to small splits;
- aggregate when necessary;
- use multi-season priors carefully.

### 3. Play-by-play is not assignment data

Public play-by-play usually does not say:

- exact route;
- blocking assignment;
- coverage assignment;
- run fit;
- read progression;
- play-call intent;
- disguised coverage;
- whether a player made a mistake.

Implication:

- player-value models for OL, DL, LB, and DB are approximate without charting/tracking;
- avoid pretending public EPA fully grades every player.

### 4. Participation data helps but does not solve attribution

Knowing who was on the field is a major public-data improvement, but it still does not identify responsibility.

Implication:

- participation-based plus-minus should be treated as an impact proxy;
- model estimates need shrinkage;
- position and role priors are essential.

### 5. Public tracking data is incomplete

NFL Next Gen Stats captures real-time location/speed/acceleration, but full raw tracking data is not broadly public. Big Data Bowl datasets are valuable but limited to specific seasons/tasks/samples.

Implication:

- tracking-derived models may not generalize to every season;
- publish them as research prototypes unless full data is available;
- avoid mixing sample tracking outputs with full-season public models without caveats.

### 6. EPA and WP are model outputs, not ground truth

Expected points and win probability are estimated from historical data and modeling choices. They can suffer from selection bias, overfitting, dependence structure, and uncertainty issues.

Implication:

- validate calibration;
- report intervals;
- avoid false precision;
- compare multiple model versions;
- do not treat tiny EPA/WP differences as definitive.

### 7. Causality is hard

A team may pass more because it is good, because it is trailing, because its defense is bad, or because the opponent forced it to pass. Observed play-calling is not randomized.

Implication:

- distinguish descriptive, predictive, and causal analysis;
- use quasi-experimental designs when possible;
- simulate counterfactuals with humility;
- validate assumptions.

## NFL data limitations

### 1. Contracts are complex

Cap hit, cash paid, guarantees, average annual value, and dead money answer different questions.

Implication:

- do not use AAV alone;
- model cap and cash separately;
- account for restructures and void years;
- snapshot contracts by date.

### 2. Team financials are private

NFL teams are private businesses, except for unique public reporting around the Green Bay Packers. Forbes and similar data are estimates.

Implication:

- call business outputs estimates;
- use robust sensitivity analysis;
- avoid overclaiming revenue causality.

### 3. Injury data is incomplete

Official injury reports are not the same as full medical data. Severity, diagnosis, long-term cost, and chronic effects may be hidden.

Implication:

- use games missed and status as proxies;
- model exposure per snap;
- do not infer medical details not in public data;
- be careful with health-related claims.

### 4. Betting lines are useful but not neutral

Markets incorporate information, but they also include bookmaker margin, public betting, limits, timing, and source differences.

Implication:

- store line timestamp and source;
- use closing lines as benchmarks;
- do not treat markets as truth.

## NCAA data limitations

### 1. Compensation is not cleanly public

There is no complete, audited, public player-level NCAA compensation table.

Implication:

- use ranges;
- separate NIL valuation from reported NIL compensation;
- separate scholarship/benefits from direct pay;
- label estimates clearly.

### 2. Finance accounting varies

EADA, MFRS, school reports, USA Today, and Knight-Newhouse may define categories differently.

Implication:

- reconcile definitions;
- document source hierarchy;
- avoid mixing categories without mapping.

### 3. Recruiting rankings are imperfect

Recruiting rankings measure prospect evaluation and market attention, not actual college value.

Implication:

- use recruiting as a prior, not a final ability measure;
- account for development, injuries, transfers, and opportunity.

### 4. Conference and schedule imbalance is large

College teams play uneven schedules with major conference-strength differences.

Implication:

- opponent adjustment is mandatory;
- include conference-year effects;
- model garbage time carefully;
- beware comparing raw production across conferences.

### 5. Transfer portal and roster churn are hard to model

College rosters change rapidly. Player identity matching can be difficult.

Implication:

- build robust player ID matching;
- model returning production and transfer inflow/outflow;
- track eligibility and class year.

## AI Coach limitations

### 1. Counterfactuals compound uncertainty

Changing one decision changes later game states, opponent response, player fatigue, injury exposure, and play-calling.

Implication:

- simulate distributions, not single alternate histories;
- compare policies across many simulations;
- communicate uncertainty.

### 2. The AI Coach may optimize the wrong objective

A real coach may account for risk, job security, player development, injury risk, morale, ownership pressure, or fan response.

Implication:

- define the objective explicitly;
- compare multiple policies: win-max, risk-averse, development-focused, health-aware.

### 3. Strategy can change opponent behavior

An aggressive fourth-down team changes defensive strategy and field-position expectations.

Implication:

- use dynamic policy simulation where possible;
- avoid assuming the opponent remains static.

## Health/labor economics limitations

### 1. Public data does not capture full health cost

Long-term neurological, orthopedic, mental-health, and post-career medical costs are not observable in standard sports data.

Implication:

- use public health-cost inflation and injury proxies carefully;
- do not infer individual medical conditions;
- frame results as aggregate labor economics.

### 2. Selection bias is severe

Players who reach the NFL are survivors of earlier injury, talent, and opportunity filters.

Implication:

- account for career survivorship;
- model exposure and attrition;
- avoid comparing active players to the general population without adjustment.

## Reporting rules

Every analysis should label itself as one of:

- descriptive;
- predictive;
- causal;
- counterfactual/simulation;
- valuation/economic estimate.

Every model output should include:

- data source;
- extraction date;
- model version;
- uncertainty;
- known limitations;
- whether the data is complete or partial.

## Strongest public-data claims

Public data can strongly support:

- play-level team efficiency;
- game-state value;
- QB and skill-position value;
- team tendencies;
- fourth-down decision quality;
- roster/cap efficiency;
- NCAA team performance;
- school-level finance analysis.

## Weakest public-data claims

Public data is weak for:

- offensive line individual grades;
- defensive coverage responsibility;
- route-level receiver value;
- play-design intent;
- full injury severity and medical cost;
- verified NCAA player compensation;
- audited NFL team revenue;
- full player tracking outside samples.
