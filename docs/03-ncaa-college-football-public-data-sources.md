# NCAA / College Football Public Data Sources

Last updated: 2026-07-08

## Summary

College football data is more API-oriented than NFL public data. The best public backbone is CollegeFootballData.com, supported by `cfbfastR` in R and `cfbd-python` in Python. The NCAA public-data landscape is strong for games, teams, drives, play-by-play, rankings, recruiting, betting lines, player stats, team stats, venues, and finance. It is weak for verified player-level compensation, private NIL deals, player tracking, and full tactical charting.

## Storage vs API expectation

| Source | Access style | Should you store it? | Reason |
|---|---:|---:|---|
| CollegeFootballData API | API key and API endpoints | Yes | API data can be revised; storing snapshots enables reproducible models and avoids rate/API dependency. |
| cfbfastR | R wrapper over CFBD + ESPN when available | Yes | Cleaned access is convenient, but raw/clean snapshots should be retained. |
| cfbd-python | Python SDK over CFBD API | Yes | Good for ingestion; not a substitute for a warehouse. |
| Sports Reference CFB | Web tables / Stathead | Yes, if used | Useful historical enrichment but should be handled carefully. |
| EADA | Public data tool / downloads | Yes | Institution finance data should be versioned by reporting year. |
| Knight-Newhouse | Public college athletics finance database | Yes | Best public structured finance source for many DI public institutions. |
| USA Today NCAA finances | Public database | Yes | Good comparison source, but definitions and years must be tracked. |
| Recruiting / roster services | API/web/CSV depending source | Yes | Recruiting rankings and roster data are revised and source-dependent. |

## Core NCAA football data sources

### 1. CollegeFootballData.com

- Main site: https://collegefootballdata.com/
- API docs: https://api.collegefootballdata.com/
- What it gives you: games, teams, conferences, drives, plays, player stats, team stats, betting lines, rankings, ratings, SP-style metrics depending endpoint, recruiting, transfer/recruit context, venues, weather, win probability, PPA, and advanced box scores.
- Access: API key required.
- Storage recommendation: store raw API responses by endpoint, season, and extraction date. Then build cleaned tables.

Example endpoint families to prioritize:

- games;
- teams;
- conferences;
- drives;
- plays / play-by-play;
- game player stats;
- game team stats;
- advanced box score;
- PPA / predicted points added;
- win probability;
- ratings;
- rankings;
- recruiting;
- betting lines;
- venues;
- weather.

### 2. cfbfastR

- URL: https://cfbfastr.sportsdataverse.org/
- What it is: an R package that wraps CollegeFootballData and ESPN live play-by-play/box scores when available.
- Why it matters: it supplies clean/tidy college football data and adds expected-points and win-probability style fields.
- Access:

```r
library(cfbfastR)

pbp <- cfbd_pbp_data(year = 2025, season_type = "regular")
games <- cfbd_game_info(year = 2025)
team_stats <- cfbd_game_team_stats(year = 2025)
player_stats <- cfbd_game_player_stats(year = 2025)
weather <- cfbd_game_weather(year = 2025)
```

For play-by-play, `cfbfastR` includes fields such as EPA, expected points before/after the play, WPA, and win probability before/after where available.

Storage recommendation: store both raw endpoint data and the enriched cfbfastR play-by-play output if you rely on cfbfastR's model fields.

### 3. cfbd-python

- URL: https://github.com/CFBD/cfbd-python
- What it is: official Python client generated from the CollegeFootballData OpenAPI spec.
- Access:

```python
import cfbd
from cfbd.rest import ApiException

configuration = cfbd.Configuration()
configuration.api_key['Authorization'] = 'YOUR_API_KEY'
configuration.api_key_prefix['Authorization'] = 'Bearer'

with cfbd.ApiClient(configuration) as api_client:
    games_api = cfbd.GamesApi(api_client)
    games = games_api.get_games(year=2025, season_type='regular')
```

Storage recommendation: ingest from Python into raw JSON and normalized Parquet tables.

### 4. Sports Reference College Football

- URL: https://www.sports-reference.com/cfb/
- What it gives you: historical college football teams, players, schedules, standings, bowls, awards, and stats.
- Best use: historical validation, older-player enrichment, awards, and public-facing reference.
- Caveat: respect terms and be careful with automated scraping. Stathead may be required for deeper querying.

### 5. NCAA / school roster and official sites

- Sources: school athletic sites, NCAA pages, conference sites.
- What they give you: rosters, bios, heights/weights, class year, hometown, previous schools, injury notes in game previews, participation notes.
- Best use: roster identity and enrichment.
- Caveat: inconsistent formatting, nonstandard IDs, and manual cleanup.

### 6. Recruiting and talent data

- Sources: CollegeFootballData recruiting endpoints, 247Sports-derived composites where available through APIs or public summaries, public recruiting rankings, transfer portal datasets.
- What they give you: prospect ratings, class rank, position, school, recruiting year, stars/rating, and team talent proxies.
- Why it matters: college football is heavily shaped by talent acquisition and development.
- Storage recommendation: store source, rating scale, recruit year, school commitment, transfer history, and canonical player matching confidence.

### 7. Betting lines and market data

- Sources: CollegeFootballData betting endpoints, odds APIs, historical line providers.
- What they give you: spread, over/under, moneyline, provider, and timing.
- Why it matters: market-implied team strength is a strong benchmark for college game prediction.
- Storage recommendation: store by game, sportsbook/provider, line type, and timestamp. Closing line is the most useful benchmark.

### 8. Weather and venue data

- Sources: CollegeFootballData venues/weather endpoints, school stadium metadata, public weather APIs.
- What they give you: venue, capacity, surface, elevation, weather, roof/open-air context, and kickoff conditions.
- Why it matters: impacts pace, passing, kicking, total points, and travel/rest analysis.

### 9. EADA

- URL: https://ope.ed.gov/athletics/
- What it gives you: institution-submitted athletics participation, revenue, and expenses under the Equity in Athletics Disclosure Act.
- Best use: public college athletics finance baselines, sport-level revenues/expenses, participation counts.
- Caveat: accounting definitions can be broad and do not necessarily match NCAA Membership Financial Reporting System data.

### 10. Knight-Newhouse College Athletics Database

- URL: https://knightnewhousedata.org/
- About data: https://knightnewhousedata.org/about-the-data
- What it gives you: public NCAA Division I college athletics revenues and expenses, based on public MFRS reports for institutions covered by the database.
- Best use: school-year finance modeling; revenue/expense categories; conference and subdivision comparisons.
- Useful categories: media rights, conference/NCAA distributions, post-season football, sponsorship/licensing, donor contributions, competition guarantees, institutional/government support, coaching compensation, facilities, recruiting, student aid, and medical expenses where available.

### 11. USA Today NCAA Finances

- URL: https://sportsdata.usatoday.com/ncaa/finances
- What it gives you: ranked revenue and expense data by school.
- Best use: cross-checking institution finance totals and building public-facing comparisons.
- Caveat: updated less frequently and definitions should be reconciled with EADA/Knight-Newhouse.

## Minimum recommended NCAA extract set

- `cfb_games`
- `cfb_teams`
- `cfb_conferences`
- `cfb_venues`
- `cfb_drives`
- `cfb_pbp`
- `cfb_team_game_stats`
- `cfb_player_game_stats`
- `cfb_advanced_box_scores`
- `cfb_ppa_team_game`
- `cfb_ppa_player_game`
- `cfb_win_probability`
- `cfb_rankings`
- `cfb_ratings`
- `cfb_recruiting_players`
- `cfb_recruiting_teams`
- `cfb_transfer_portal_public`
- `cfb_betting_lines`
- `cfb_weather`
- `eada_finance`
- `knight_newhouse_finance`
- `usa_today_ncaa_finance`

## College football-specific modeling features

College football requires features that are less central in the NFL:

- recruiting class strength;
- transfer portal inflows/outflows;
- returning production;
- conference strength;
- schedule imbalance;
- bowl/playoff incentive context;
- redshirt/class-year status;
- coaching changes;
- NIL/revenue-sharing context;
- roster churn;
- scholarship/roster limits;
- school athletic department finance;
- media/conference distribution changes.

## Recommended ingestion approach

1. Use CFBD API as the canonical public NCAA football source.
2. Ingest through `cfbfastR` or `cfbd-python` depending project language.
3. Store raw API results and transformed tables.
4. Build ID matching between CFBD player IDs, school rosters, Sports Reference IDs, recruiting IDs, and draft/NFL IDs.
5. Store finance data separately at institution-year and sport-year grain.
6. Build a school-season roster/talent table that links recruiting, returning production, transfers, and player production.
7. Build team-style and play-calling features from play-by-play.

## Important NCAA caveat

Public college football data is strong for performance and team-level finance. It is weak for verified player-level compensation. NIL estimates and reported deals are not the same thing as actual compensation. Direct school revenue-sharing data may become more structured after House v. NCAA implementation, but public player-level visibility is still incomplete.
