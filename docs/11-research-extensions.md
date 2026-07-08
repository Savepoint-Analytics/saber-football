# Research Extensions: AI Coach, Health-Cost Labor Economics, and NCAA Hockey Compensation

Last updated: 2026-07-08

## Summary

The core football sabermetrics thesis can support three higher-order research programs:

1. Simulating how an AI Coach would run a team compared with actual play-by-play management.
2. Studying football compensation against injury risk and health-care cost inflation as labor economics.
3. Estimating what player-level compensation should be for NCAA hockey players, using sport finance, player contribution, and revenue-sharing constraints.

The third item mentions NCAA hockey rather than football. This file documents it as a valid related sports-economics extension. If the intended sport was NCAA football, the same framework applies with football-specific performance and finance inputs.

---

# 1. AI Coach Simulation

## Research question

> How would a team have performed if an AI Coach made play-by-play management decisions instead of the actual coaching staff?

## Definition

An AI Coach is a decision policy, not an artificial personality. It takes game state and roster context as inputs and returns an action.

Example actions:

- go for it / punt / kick on fourth down;
- attempt two-point conversion / kick extra point;
- pass / run;
- tempo / huddle / no-huddle;
- timeout / no timeout;
- field goal attempt / punt / offensive play;
- personnel grouping;
- risk-seeking or risk-averse strategy.

## Data needed

- play-by-play;
- EPA/WP/WPA;
- down/distance/yardline/time/score;
- timeouts;
- weather/stadium;
- team strength;
- QB/player availability;
- injuries;
- personnel participation where available;
- historical play outcome distributions;
- actual coach decisions.

## Model components

### State model

```text
state_t = {
  score,
  time,
  down,
  distance,
  yardline,
  possession,
  timeouts,
  weather,
  team_strength,
  player_availability,
  personnel,
  game_script
}
```

### Action model

Possible actions:

```text
action_t ∈ {run, pass, punt, field_goal, go_for_it, xp, two_point, timeout, no_timeout, tempo}
```

### Transition model

```text
P(state_{t+1} | state_t, action_t, teams, players, context)
```

### Reward model

Possible objectives:

- expected points;
- win probability;
- expected wins;
- playoff probability;
- injury-adjusted wins;
- player development;
- revenue/fan engagement;
- conservative downside protection.

## Modeling approaches

### Baseline simulation

Sample historical outcomes from similar game states.

Pros:

- easy to implement;
- transparent;
- grounded in real football outcomes.

Cons:

- limited by historical sample sizes;
- difficult for rare states;
- does not fully account for opponent adaptation.

### Markov decision process

Use game states, actions, transition probabilities, and rewards.

Pros:

- natural for football decisions;
- supports policy comparison;
- can model risk preferences.

Cons:

- state space can explode;
- transition model quality matters;
- tactical details are partially hidden.

### Offline reinforcement learning / policy evaluation

Estimate how alternative policies would perform using logged historical play data.

Pros:

- directly addresses counterfactual coaching;
- can evaluate real-vs-AI policy.

Cons:

- strong off-policy bias risk;
- actions are not randomized;
- support mismatch if AI recommends actions rarely seen historically.

### Inverse optimization / risk preference modeling

Infer what objective coaches appear to optimize.

Pros:

- distinguishes conservative risk preference from irrationality;
- useful for coach profiling.

Cons:

- assumptions about objective function are strong.

## AI Coach deliverables

- actual decision log;
- AI recommended decision log;
- decision disagreement table;
- WP/EPA difference with uncertainty;
- simulated game outcome distribution;
- season-level counterfactual wins;
- coach risk-preference profile;
- team-specific AI Coach strategy report.

## Example output

```text
Team: DET
Season: 2025
AI Coach Objective: maximize mean win probability
Actual wins: 11
Simulated AI wins: 11.6 [10.3, 12.8]
Largest decision gaps: fourth-and-short near midfield, red-zone fourth downs, late-half timeout use
Conclusion: AI policy likely adds modest win value, but most decisions fall within uncertainty bands.
```

---

# 2. Football Pay, Injury Risk, and Health-Cost Inflation

## Research question

> Does football compensation adequately account for injury risk, career-shortening risk, and health-care cost inflation?

## Why this matters

Football is dangerous. Compensation should not be analyzed only as payment for performance. It also compensates for physical risk, career volatility, future medical expenses, and bargaining power under league/NCAA rules.

## Key concepts

### Risk-adjusted compensation

```text
risk_adjusted_pay = cash_compensation - expected_injury_cost - expected_lost_future_earnings
```

### Injury exposure

```text
injury_rate = injuries / snaps_or_games_exposed
```

### Career earnings at risk

```text
career_value_lost = expected_future_contract_value_without_injury - realized_future_contract_value_after_injury
```

### Health-cost inflation adjustment

```text
real_health_adjusted_compensation = compensation / medical_cost_index
```

## Data sources

### Performance and exposure

- nflverse play-by-play;
- snap counts;
- participation;
- player stats;
- position;
- age;
- career length.

### Injuries

- nflreadr injury reports;
- official NFL injury reports;
- injured reserve transactions;
- games missed;
- public injury datasets;
- CBA-era rule changes.

### Compensation

- NFLPA salary cap reports;
- OverTheCap;
- Spotrac;
- guaranteed money;
- cash paid;
- dead money;
- pension/benefit structures if available.

### Health-cost context

- medical care CPI;
- employer health plan cost inflation;
- workers' compensation context;
- CBA benefit documents;
- public health economics literature.

## Model designs

### Position risk premium model

```text
log(cash_paid_it) =
  player_quality_it
+ position_risk_premium_position
+ age
+ experience
+ draft_capital
+ availability
+ team/year effects
+ error
```

Question: are high-risk positions paid a premium after controlling for performance?

### Injury cost model

```text
expected_injury_cost =
  P(injury | position, age, snaps, history)
* expected_games_missed
* salary_per_game
+ expected_future_earnings_loss
+ estimated_medical_cost
```

### CBA / rule-change event study

Use CBA and rule changes as interventions.

```text
injury_rate_it =
  position_fixed_effect
+ season_fixed_effect
+ post_policy_indicator
+ exposure
+ error
```

### Undercompensation index

```text
undercompensation_index =
  estimated_player_value_created
- realized_compensation
- expected_health_and_career_cost
```

## Deliverables

- injury risk by position and age;
- career length by position;
- salary-risk premium estimates;
- guaranteed-money protection by risk profile;
- medical-cost inflation adjusted earnings;
- CBA-era injury and pay comparison;
- labor economics research paper outline.

## Ethical and analytical caveats

- Do not infer individual medical diagnoses from public data.
- Avoid sensational framing.
- Report aggregate patterns.
- Separate short-term injury from long-term health cost.
- Make uncertainty explicit.

---

# 3. Estimating Player-Level Compensation for NCAA Hockey Players

## Research question

> What should NCAA hockey players be paid, based on their estimated contribution to program revenue, competitive success, scholarship value, roster constraints, NIL value, and direct revenue-sharing rules?

## Why hockey is different from football

NCAA hockey has:

- smaller rosters;
- different revenue scale;
- fewer public analytics datasets;
- a meaningful Canadian/international player pipeline;
- different NIL dynamics;
- scholarship and roster-limit changes under the post-House environment;
- less public player-level compensation reporting.

## Data sources

### Finance

- EADA: https://ope.ed.gov/athletics/
- Knight-Newhouse: https://knightnewhousedata.org/about-the-data
- school athletic department reports;
- open records requests;
- Extra Points MFRS-derived hockey budget reporting where available;
- USA Today NCAA finances for athletic department context.

### Policy

- College Hockey Inc. House settlement FAQ: https://www.collegehockeyinc.com/2025/06/chi-house-settlement-qa/
- College Sports Commission revenue sharing: https://www.collegesportscommission.org/revenue-sharing/
- House v. NCAA summaries.

### Player performance

Potential sources:

- NCAA official stats;
- College Hockey News;
- Elite Prospects;
- team sites;
- conference stats;
- NHL Central Scouting;
- NHL draft data;
- play-by-play/shift/shot data if available from vendors or public feeds.

### Research

- SSRN paper on top-flight men’s college hockey rents: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2025919
- Hockey plus-minus modeling literature, such as regularized logistic regression for player contribution: https://arxiv.org/abs/1209.5026

## Compensation components

```text
estimated_hockey_player_compensation =
  scholarship_value
+ direct_revenue_share_estimate
+ NIL_estimate
+ development_value
+ marginal_revenue_product
+ roster_retention_value
```

## Sport-level pool model

Estimate how much money a school could rationally allocate to hockey.

```text
hockey_compensation_pool =
  min(
    school_revenue_sharing_pool * hockey_allocation_rate,
    hockey_program_revenue * athlete_share_rate,
    donor_or_collective_hockey_pool + direct_school_allocation
  )
```

Possible allocation rates:

- revenue share of athletic department;
- profit contribution;
- roster share;
- competitive priority;
- Title IX/equity constraint;
- donor-designated sport funding.

## Player-level allocation model

```text
player_weight =
  performance_value_weight
+ ice_time_role_weight
+ position_scarcity_weight
+ NHL_draft_value_weight
+ recruiting_retention_weight
+ NIL_brand_weight
+ leadership_weight
```

Then:

```text
player_compensation_estimate =
  hockey_compensation_pool * player_weight / sum(player_weights)
```

## Hockey performance value options

### Simple public approach

- goals;
- assists;
- points;
- shots;
- goalie save percentage;
- games played;
- plus/minus with caution;
- awards;
- draft status;
- team success.

### Better approach

- even-strength goal differential while on ice;
- shot differential while on ice;
- expected-goal differential if available;
- special-teams role;
- goalie-adjusted defensive impact;
- regularized plus-minus;
- opponent and teammate adjustment;
- NHL/draft/development value.

### Best approach

- shift-level data;
- event-level shot/play data;
- player tracking if available;
- adjusted regularized plus-minus;
- expected goals and possession value;
- recruiting/development pipeline value.

## Compensation outputs

For each player:

- low estimate;
- midpoint estimate;
- high estimate;
- scholarship value;
- NIL estimate;
- direct-pay estimate;
- marginal revenue product estimate;
- confidence score;
- source quality grade.

## Example structure

```text
Player: First Last
School: Example University
Sport: Men's Ice Hockey
Season: 2026-27
Role: Top-line forward
Scholarship value: $45,000
Direct-pay estimate: $12,000–$55,000
NIL estimate: $2,000–$20,000
Total economic compensation estimate: $59,000–$120,000
Confidence: medium-low
Reason: strong role and draft value, but direct player-level compensation data unavailable.
```

## Important caveats

1. NCAA hockey compensation should be estimated as ranges.
2. International player NIL/payment rules may complicate estimates.
3. Public hockey analytics data is thinner than football, basketball, or NHL data.
4. EADA sport-level accounting may not reflect true program economics.
5. Title IX and school-specific policy constraints remain important.
6. If using open records, MFRS data may be better than EADA, but availability varies by public/private school.

## How this connects back to football

The same logic can estimate football compensation, but with better performance data and larger revenue pools. Football has stronger public play-by-play data; hockey may have more compensation uncertainty and more performance-data limitations.
