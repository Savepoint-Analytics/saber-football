# Modeling Roadmap for an American Football Sabermetrics Project

Last updated: 2026-07-08

## Core thesis

> Estimate team and player value from play-level changes in expected points and win probability, adjust for context, teammates, opponents, tactics, injuries, and roster cost, then connect those estimates to wins, salary efficiency, and team/program revenue.

## Product vision

Build a football analytics system that answers five classes of questions:

1. **What happened?** Team/player efficiency, play value, tactics, and roster usage.
2. **Why did it happen?** Context-adjusted performance, matchup effects, injuries, tactics, and personnel.
3. **Who created value?** Player, unit, and coach impact on points and wins.
4. **Was it worth the cost?** Salary/cap/NIL/revenue-sharing efficiency.
5. **What would have happened under another strategy?** AI Coach simulation and counterfactual play-calling.

## Phase 0 — Project foundation

### Goals

- Define canonical metrics.
- Build data ingestion.
- Establish reproducibility.

### Deliverables

- source registry;
- raw data snapshots;
- data dictionaries;
- `dim_game`, `dim_team`, `dim_player`, `fact_play`;
- quality checks;
- baseline dashboards.

### Success criteria

- Can rebuild a season of NFL play-by-play metrics from raw data.
- Can reproduce EPA/WPA aggregation by team, game, week, and season.
- Can compare outputs to public nflverse examples.

## Phase 1 — Descriptive team analytics

### Goals

Understand how teams play and how efficient they are.

### Features

- EPA/play;
- WPA;
- success rate;
- explosive-play rate;
- pass rate over expected;
- early-down pass rate;
- neutral-script pass rate;
- tempo;
- fourth-down aggressiveness;
- red-zone efficiency;
- pressure/box/personnel context where available;
- opponent-adjusted team efficiency.

### Deliverables

- team efficiency dashboard;
- team style dashboard;
- weekly trend reports;
- matchup previews.

## Phase 2 — Player performance models

### Goals

Estimate individual player contribution by role and context.

### Models

- QB value model;
- rusher value model;
- receiver value model;
- special teams EPA model;
- participation-based on/off model;
- player-game opportunity model.

### Deliverables

- player EPA leaderboard;
- QB value report;
- skill-position opportunity report;
- position-specific player cards;
- player availability/injury adjustment.

## Phase 3 — Team strength and game prediction

### Goals

Predict game outcomes and estimate true team strength.

### Model targets

- win probability;
- point margin;
- total points;
- team offensive/defensive EPA;
- drive outcome;
- game script.

### Features

- team EPA/PPA;
- opponent-adjusted efficiency;
- rest/travel;
- injuries;
- weather/stadium;
- market spread and total;
- roster strength;
- recent form with shrinkage;
- QB availability.

### Model classes

- Elo/Glicko;
- ridge/logistic regression;
- gradient boosting;
- Bayesian hierarchical ratings;
- market-informed priors;
- simulation.

### Deliverables

- power ratings;
- game prediction model;
- market benchmark comparison;
- calibration report.

## Phase 4 — Player value and WAR

### Goals

Translate player contribution into wins and roster value.

### Steps

1. Estimate player points above average.
2. Define position-specific replacement level.
3. Convert points to wins.
4. Add uncertainty intervals.
5. Join salary/cap/cash cost.
6. Estimate surplus value.

### Deliverables

- public-data WAR prototype;
- replacement baseline report;
- player surplus-value table;
- positional market efficiency report;
- rookie contract value report.

## Phase 5 — Tactical and coaching models

### Goals

Evaluate decisions, play-calling, and coaching style.

### Models

- fourth-down decision model;
- two-point conversion model;
- field goal/punt/go model;
- pass/rush choice model;
- play-action/motion value model where data exists;
- personnel package efficiency;
- coach risk-preference model.

### Deliverables

- coaching aggressiveness dashboard;
- decision quality report;
- fourth-down recommendation table with uncertainty;
- play-calling tendency model;
- team tactical fingerprints.

## Phase 6 — AI Coach simulation

### Goal

Simulate how an AI Coach would run a team compared with actual play-by-play management.

### AI Coach definition

The AI Coach is not a generic chatbot. It is a policy engine that recommends decisions under football constraints.

Core decision points:

- go/punt/kick on fourth down;
- two-point vs extra point;
- pass vs run choice;
- tempo/no-huddle choice;
- timeout usage;
- field goal range decisions;
- aggression by score/time state;
- personnel package selection where data supports it.

### Simulation approach

1. Represent every game state.
2. Train outcome models for play, drive, and game transitions.
3. Define actual coach policy from historical decisions.
4. Define AI Coach policy from expected value, risk preference, or custom objective.
5. Replay historical games with counterfactual decisions.
6. Simulate many trajectories to estimate distribution of outcomes.
7. Compare actual vs AI Coach outcomes.

### Policy objectives

Possible AI Coach objectives:

- maximize mean win probability;
- maximize median outcome;
- maximize conservative quantile outcome;
- maximize expected points;
- minimize injury exposure;
- maximize development reps;
- maximize fan/revenue value;
- balance short-term win probability with long-term roster health.

### Deliverables

- AI Coach policy table;
- counterfactual game simulator;
- actual-vs-AI decision report;
- win impact estimate;
- risk preference comparison;
- team-specific AI Coach effectiveness report.

## Phase 7 — Revenue and salary efficiency

### Goals

Connect wins, player value, and roster construction to business outcomes.

### NFL models

- team revenue panel;
- franchise value panel;
- salary cap efficiency;
- player contract surplus;
- positional spending efficiency;
- playoff value;
- QB/star-player revenue value.

### NCAA models

- school finance panel;
- football revenue model;
- recruiting ROI;
- revenue-sharing allocation model;
- compensation efficiency model;
- donor/media/conference distribution model.

### Deliverables

- NFL roster ROI dashboard;
- NFL contract surplus report;
- NCAA football finance model;
- performance-to-revenue report;
- compensation allocation model.

## Phase 8 — Injury, health cost, and labor economics

### Goals

Study whether player pay adequately compensates health risk, especially as health-care costs inflate.

### Questions

- Which positions bear the highest injury risk per snap?
- How does salary compensate for injury risk?
- Are dangerous roles undercompensated after accounting for career length?
- How much career value is lost to injury?
- How do medical-cost inflation and CBA benefits affect real compensation?
- How much do teams externalize long-term health costs?

### Data

- injuries;
- games missed;
- snap exposure;
- position;
- age;
- salary/cash/cap;
- contract guarantees;
- career length;
- health-care inflation indices;
- CBA benefit rules;
- workers' compensation where available.

### Deliverables

- injury risk by position;
- salary-risk premium model;
- health-cost inflation adjustment;
- career earnings at risk model;
- labor economics research note.

## Phase 9 — NCAA compensation estimation

### Goals

Estimate fair or economically implied player compensation where actual compensation is not fully public.

### NCAA football

- estimate sport-level direct-pay pools;
- estimate player weights from production, role, recruiting value, roster scarcity, and NIL brand;
- produce low/mid/high compensation ranges;
- compare compensation to estimated marginal revenue product.

### NCAA hockey extension

- estimate hockey program revenue and expenses;
- allocate revenue-sharing pool under school/sport constraints;
- estimate player contribution using hockey-specific plus-minus, shot, goal, and shift data where available;
- account for scholarship expansion and roster caps;
- produce player-level fair compensation ranges.

### Deliverables

- compensation caveat report;
- NCAA football compensation estimator;
- NCAA hockey compensation estimator;
- Title IX/legal uncertainty caveat;
- school/sport allocation simulator.

## Phase 10 — Advanced tracking and video research

### Goals

Use Big Data Bowl and future tracking/video sources to model football actions invisible in play-by-play.

### Models

- expected yards during play;
- route classification;
- coverage classification;
- pass-rush pressure model;
- tackle probability;
- pursuit angle;
- spacing and motion value;
- player trajectory counterfactuals.

### Deliverables

- Big Data Bowl research notebooks;
- tracking-derived player metrics;
- spatial tactical reports;
- AI Coach spatial extensions.

## MVP recommendation

Build in this order:

1. NFL play-by-play warehouse.
2. Team EPA/style dashboards.
3. QB and skill player value models.
4. Participation-based on/off model.
5. Contract ROI model.
6. NCAA CFBD ingestion and team PPA model.
7. NCAA finance ingestion.
8. AI Coach fourth-down simulator.
9. Injury and labor economics model.
10. NCAA compensation estimator.
