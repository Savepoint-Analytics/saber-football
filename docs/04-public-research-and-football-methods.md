# Public Research and Methods That Apply to American Football

Last updated: 2026-07-08

## Summary

American football sabermetrics must be built around play value, field position, clock, down/distance, player interaction, tactical decision-making, and roster cost. Baseball-style isolated event valuation does not transfer directly because football is a multi-agent, high-dependence, low-sample, role-specialized sport. The right methods are expected points, win probability, player-on-field models, replacement value, tactical simulations, roster economics, and uncertainty-aware decision modeling.

## Foundational concepts

### Expected Points

Expected Points estimates the expected value of a game state in points. Typical inputs include:

- down;
- distance;
- yard line;
- time remaining;
- score differential;
- possession;
- half/game period;
- home/away;
- team strength;
- weather/venue;
- timeout state;
- and sometimes market-implied team strength.

Expected Points Added is:

```text
EPA = EP_after_play - EP_before_play
```

EPA is the core public football value metric because it values every play on the same scale.

### Win Probability

Win Probability estimates the chance of winning from the current game state. Win Probability Added is:

```text
WPA = WP_after_play - WP_before_play
```

WPA is useful for game-management decisions, leverage, and translating play outcomes into wins. EPA is usually more stable for player/team evaluation; WPA is more context-sensitive and situational.

### Success Rate

Success rate is a binary efficiency measure. Common definitions:

- first down: successful if it gains at least 40% of yards to go;
- second down: at least 60%;
- third/fourth down: conversion.

Success rate complements EPA by identifying consistency, not just explosive-play value.

### Explosive-play rate

Common thresholds:

- pass: 15+ or 20+ yards;
- rush: 10+ or 12+ yards.

This is especially useful for team identity and defensive vulnerability.

### Completion Percentage Over Expected

CPOE compares observed completion rate to expected completion rate after accounting for throw difficulty. It is a better QB accuracy measure than raw completion percentage.

### Predicted Points Added in college football

CollegeFootballData and cfbfastR often use PPA / predicted points added as a college-football analogue to EPA.

## Public research foundation

### nflWAR

Source: https://arxiv.org/abs/1802.00998

Ronald Yurko, Samuel Ventura, and Maksim Horowitz introduced `nflWAR`, a reproducible player-evaluation framework for offensive skill players using publicly available NFL play-by-play, expected points, win probability, and multilevel models. The paper is important because it frames football player value in wins above replacement while explicitly discussing uncertainty and football-specific limitations.

Use in this project:

- baseline for public-data WAR;
- player value above replacement;
- uncertainty-aware player evaluation;
- offensive skill-player modeling;
- extension to other positions when player-on-field participation data is available.

### Expected Points model critique and uncertainty

Source: https://arxiv.org/abs/2409.04889

Recent research argues that expected-points models built with machine learning can suffer from selection bias, overfitting artifacts, missing uncertainty quantification, and dependency problems in football play-by-play data.

Use in this project:

- report intervals, not just point estimates;
- avoid claiming that EPA is a perfect causal value;
- use hierarchical/statistical models where possible;
- validate EP and WP calibration by season and game state;
- consider catalytic priors or smoothing for unstable game states.

### Fourth-down decision-making with uncertainty

Source: https://arxiv.org/abs/2311.03490

Fourth-down decision models often maximize estimated win probability. But decision recommendations can be unstable because WP estimates are uncertain. Recent research emphasizes bootstrapped uncertainty and humility in fourth-down recommendations.

Use in this project:

- recommend go/kick/punt with confidence bands;
- label decisions as clearly better, toss-up, or risk-preference-dependent;
- avoid pretending a 0.2 percentage point WP edge is definitive;
- evaluate coaches against an uncertainty-aware decision frontier.

### Risk preferences and inverse decision modeling

Source: https://arxiv.org/abs/2309.00756

An inverse optimization approach can infer the risk preferences behind observed fourth-down decisions. This is valuable because coaches may not optimize mean win probability; they may optimize a conservative quantile of outcome distribution.

Use in this project:

- estimate coach risk tolerance;
- compare actual coach behavior against an AI Coach policy;
- distinguish "bad decision" from "conservative objective function";
- model whether teams become more aggressive over time.

### Simulation-based decision-making with NFLSimulatoR

Source: https://arxiv.org/abs/2102.01846

Simulation-based methods can evaluate in-game strategies and rule changes by sampling from historical play-by-play data. This is directly relevant to AI Coach simulation.

Use in this project:

- simulate counterfactual fourth-down decisions;
- simulate pass/rush mix changes;
- simulate drive policies;
- compare actual play-calling to alternative policies;
- stress-test coaching strategies against realistic play distributions.

### Continuous-time within-play valuation with tracking data

Source: https://arxiv.org/abs/1906.01760

Tracking data enables valuation within a play, not just before and after the play. Models can estimate expected yards or expected value from player locations and trajectories.

Use in this project:

- Big Data Bowl tracking work;
- expected yards during run/pass plays;
- route/coverage/spatial pressure modeling;
- tackle probability;
- receiver separation and route value;
- pass-rush influence.

### Fractional tackles and tracking-based defensive credit

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11739690/

Tracking-based work can allocate defensive credit more granularly than traditional tackle counts. This matters because box-score tackles can mislead: one player may finish a tackle, while others constrained the runner.

Use in this project:

- tackle probability models;
- defender responsibility and credit allocation;
- open-field tackling value;
- pursuit-angle and leverage models.

### Combine and draft prediction

Source: https://arxiv.org/abs/2303.05774

Research on the NFL Scouting Combine suggests combine data can help predict whether a player reaches NFL participation, but it is much weaker at predicting long-term NFL success.

Use in this project:

- draft model should combine production, age, draft capital, position, combine, and college context;
- do not over-weight athletic testing;
- model different targets separately: drafted, makes roster, plays snaps, becomes starter, produces surplus value.

### Injury and CBA research

Source: https://arxiv.org/abs/1805.01271

Research has examined NFL injuries before and after the 2011 CBA practice restrictions. The broader lesson is that football injury data must be modeled with rule changes, CBA changes, reporting changes, and exposure changes.

Use in this project:

- injury risk by exposure/snap, not only by season;
- injury cost by salary and medical cost inflation;
- labor economics around risk compensation;
- policy evaluation across CBA/rule eras.

## Methods that apply well to American football

### 1. Expected points and win probability models

Best for:

- play valuation;
- player/team contribution;
- game-state decision-making;
- fourth-down decisions;
- two-point conversion decisions;
- field goal/punt/go decisions;
- drive simulation.

Model classes:

- multinomial logistic regression;
- generalized additive models;
- gradient boosted trees;
- Bayesian hierarchical models;
- calibrated classification/regression;
- Markov decision processes;
- simulation models.

### 2. Opponent-adjusted team ratings

Best for:

- team strength;
- schedule imbalance;
- college conference imbalance;
- playoff/season simulation.

Methods:

- Elo / Glicko;
- margin-of-victory ratings;
- hierarchical team-season ratings;
- adjusted EPA/PPA;
- Bayesian power ratings;
- market-informed ratings using spreads.

### 3. Play-calling and tactical tendency models

Best for:

- pass rate over expected;
- run/pass tendency;
- tempo;
- fourth-down aggressiveness;
- personnel package efficiency;
- coaching identity.

Methods:

- classification models for play type;
- counterfactual outcome models;
- policy evaluation;
- inverse reinforcement learning;
- Markov decision processes;
- causal forests/uplift for tactical effects with caution.

### 4. Player-on-field adjusted models

Best for:

- value of non-ball-carriers;
- offensive line and defensive value proxies;
- player interaction effects;
- lineup impact.

Methods:

- regularized adjusted plus-minus;
- hierarchical Bayesian partial pooling;
- crossed random effects for player, team, opponent, coach;
- shrinkage priors by position and role;
- possession/play-level EPA outcomes.

### 5. Replacement-value and WAR-style models

Best for:

- comparing positions on a wins scale;
- translating performance to roster decisions;
- salary efficiency;
- draft and free-agent evaluation.

Methods:

- position-specific replacement baselines;
- opportunity-adjusted EPA;
- wins conversion using points-to-wins or WPA;
- resampling uncertainty;
- role-adjusted baselines.

### 6. Tracking-derived spatial models

Best for:

- expected yards;
- receiver separation;
- route value;
- coverage classification;
- pass rush;
- tackle probability;
- motion and spacing.

Methods:

- sequence models;
- graph neural networks;
- spatiotemporal embeddings;
- density estimation;
- deep learning with interpretable summaries;
- counterfactual trajectory simulation.

Public limitation: only Big Data Bowl samples are broadly accessible.

### 7. Revenue and labor economics models

Best for:

- performance-to-revenue links;
- salary-cap efficiency;
- injury compensation;
- player surplus value;
- NCAA revenue sharing.

Methods:

- panel data with team/school fixed effects;
- event studies;
- difference-in-differences;
- structural revenue allocation models;
- counterfactual salary allocation;
- player marginal revenue product estimation.

## Methods to avoid or treat carefully

- Raw yards per game without pace/opponent/game script adjustment.
- Raw touchdowns as a stable player-value metric.
- QB wins.
- Unadjusted plus-minus or on/off models without teammates/opponents.
- Treating EPA as causal without accounting for play selection.
- Using betting markets as ground truth instead of a strong benchmark/feature.
- Overfitting coaching/tactic models on small samples.
- Equating NIL valuations with actual compensation.
- Using college team finance as if every school uses identical accounting rules.

## Project method hierarchy

1. Descriptive football metrics: EPA, WPA, success rate, explosive rate.
2. Context-adjusted efficiency: opponent, game state, venue, weather, rest.
3. Player/team attribution: participation, role, position, teammates, opponents.
4. Replacement value: translate contribution into wins.
5. Cost/value: salary, cap hit, contract surplus, NIL/revenue-sharing context.
6. Tactical simulation: compare actual decisions to AI Coach policies.
7. Business/labor economics: connect wins and health risk to revenue and compensation.
