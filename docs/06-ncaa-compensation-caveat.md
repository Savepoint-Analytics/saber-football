# NCAA Compensation Caveat

Last updated: 2026-07-08

## Summary

NCAA athlete compensation is in transition. College football and other Division I sports now operate in a post-House v. NCAA environment where schools may directly share revenue with athletes, subject to annual institutional caps, while athletes may also receive third-party NIL compensation. However, verified player-level compensation data is still not publicly available in a clean, complete, audited format.

This means NCAA compensation modeling should be framed as estimation, not salary measurement.

## Current compensation landscape

### Direct school revenue sharing

Under the House v. NCAA settlement framework, Division I schools that opt in may directly share revenue with student-athletes. Public summaries have described the initial 2025-26 school cap as approximately $20.5 million per institution, with the cap expected to rise over time.

Primary references:

- NCSL summary: https://www.ncsl.org/resources/details/what-the-ncaa-settlement-means-for-colleges-and-state-legislatures
- College Sports Commission revenue-sharing information: https://www.collegesportscommission.org/revenue-sharing/

### NIL compensation

Athletes may earn name, image, and likeness compensation from third parties. NIL can include:

- endorsements;
- social-media sponsorships;
- appearances;
- camps;
- autographs;
- local business deals;
- collective-facilitated deals;
- donor-backed deals.

After the settlement, NIL deals above a reporting threshold may be subject to review through the new governance structure to assess whether they represent legitimate NIL value rather than disguised pay-for-play.

### Scholarships and benefits

Scholarships, cost-of-attendance benefits, educational awards, meals, and other benefits should be tracked separately from direct pay and NIL. They are part of economic compensation but are not the same as salary.

## Why NCAA compensation data is difficult

| Problem | Explanation |
|---|---|
| No complete public player-level salary table | Unlike the NFL, NCAA athletes do not have a universal public salary/cap database. |
| NIL valuations are not compensation | Public NIL valuations estimate brand/market value, not necessarily actual cash received. |
| Reported deals are selective | Media-reported NIL deals overrepresent star athletes and unusual deals. |
| School revenue sharing may not be fully public by athlete | Schools may report aggregate or compliance data without publishing player-level details. |
| Title IX uncertainty | How direct payments and NIL-related support interact with Title IX remains legally and operationally contested. |
| International athletes | Visa/status issues can complicate NIL and direct compensation for non-U.S. athletes. |
| Sport allocation is strategic | Schools may allocate revenue sharing across football, basketball, women’s sports, Olympic sports, roster retention, and recruiting needs. |
| Accounting definitions vary | Athletic department finance data differs across EADA, MFRS, Knight-Newhouse, USA Today, and school reports. |

## Recommended compensation categories

Do not collapse everything into one field. Use separate categories:

```text
total_player_economic_value =
  scholarship_value
+ cost_of_attendance
+ direct_school_revenue_share
+ third_party_nil_cash
+ third_party_nil_non_cash
+ educational_awards
+ housing_meals_medical_benefits
+ insurance_or_health_benefits
```

In practice, many of these will be estimated or missing.

## Recommended data model

### institution_year_compensation_context

- `school_id`
- `fiscal_year`
- `division`
- `conference`
- `opt_in_status`
- `revenue_sharing_cap`
- `reported_total_revenue_shared`
- `reported_sport_allocation_football`
- `reported_sport_allocation_mbb`
- `reported_sport_allocation_wbb`
- `reported_sport_allocation_other`
- `title_ix_policy_notes`
- `source_url`
- `source_date`

### athlete_compensation_estimate

- `athlete_id`
- `school_id`
- `sport`
- `season`
- `position`
- `scholarship_estimated_value`
- `direct_pay_estimate_low`
- `direct_pay_estimate_mid`
- `direct_pay_estimate_high`
- `nil_estimate_low`
- `nil_estimate_mid`
- `nil_estimate_high`
- `reported_nil_deal_flag`
- `reported_nil_amount`
- `valuation_source`
- `confidence_level`
- `notes`

### sport_allocation_model

- `school_id`
- `fiscal_year`
- `sport`
- `sport_revenue`
- `sport_expense`
- `roster_size`
- `scholarship_count`
- `media_value_proxy`
- `attendance_proxy`
- `competitive_importance_score`
- `title_ix_constraint_flag`
- `estimated_pool_allocation`

## How to estimate NCAA football player compensation

### Conservative approach

Use only verified public reports:

- school-reported revenue sharing totals;
- public NIL deal reports;
- scholarship values;
- EADA/Knight finance data;
- roster and scholarship counts.

Output ranges, not point estimates.

### Market-value approach

Estimate marginal value created by player:

```text
player_compensation_target =
  player_marginal_win_value
+ player_brand_value
+ player_retention_value
+ player_recruiting_replacement_cost
```

Inputs:

- player PPA/EPA/WAR estimate;
- position;
- team revenue;
- conference/media environment;
- attendance and donor base;
- recruiting replacement cost;
- NIL social/brand metrics;
- role/star status;
- transfer risk.

### Revenue-share allocation approach

Estimate sport and player pools:

```text
school_revenue_share_pool = min(allowed_cap, school_budgeted_direct_pay)
football_pool = school_revenue_share_pool * football_allocation_rate
player_share = football_pool * player_weight / sum(player_weights)
```

Player weights can combine:

- snap share;
- position market value;
- PPA/WAR contribution;
- recruiting rank;
- eligibility remaining;
- transfer-market risk;
- leadership/star status;
- NIL brand score.

## Important language to use

Use:

- "estimated compensation";
- "reported compensation";
- "implied market value";
- "direct school revenue-sharing estimate";
- "NIL valuation";
- "scholarship and benefits value";
- "compensation range".

Avoid:

- "salary" unless referring to direct pay in a clearly defined setting;
- "actual NIL earnings" unless verified;
- "market value" without explaining the model;
- single-point estimates without uncertainty.

## Project implication

For NCAA football, performance modeling can be much stronger than compensation modeling. Build the performance side first. Then layer compensation as a range-based economic estimate with explicit caveats.

## If estimating NCAA hockey compensation

If the project extends to NCAA hockey, the caveats become even more important because player-level compensation data is thinner than football.

Useful hockey-specific references:

- College Hockey Inc. House settlement FAQ: https://www.collegehockeyinc.com/2025/06/chi-house-settlement-qa/
- EADA data tool: https://ope.ed.gov/athletics/
- Knight-Newhouse finance data: https://knightnewhousedata.org/about-the-data
- Research on men’s college hockey rents: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2025919

College Hockey Inc. has noted that Division I hockey programs opting into the settlement may have a roster cap of 26 players and may grant up to 26 full athletic scholarships in addition to revenue-sharing and NIL opportunities. This makes scholarship value, roster size, and revenue-sharing allocation key parts of any compensation estimate.
