# NFL identity, participation, and EPA review

Descriptive review of the pinned 2024 and 2025 nflverse snapshots. The portable manifests
under `manifests/nfl/` identify the inputs by path and SHA-256.

## Player IDs

PFR snap counts use PFR player IDs. FTN participation via nflverse lists GSIS IDs and
names for the same games. The reviewed snap aliases below pair those identifiers using
matching game, team, name, and position, with roster or official name evidence where
needed. Each player's existing nflverse PFR ID remains in the bridge alongside the alias.
The join requires each PFR ID to identify at most one player.

| Snap ID | GSIS ID | Player | Evidence |
|---|---|---|---|
| AndeAl01 | 00-0037428 | Alec Anderson | BUF participation in 20 of 20 source games in 2024 and 19 of 19 in 2025. Same-team roster match. |
| CoopBu00 | 00-0039245 | Ryan “Bump” Cooper Jr. | BAL participation in the one source game. The [Ravens media guide](https://static.www.nfl.com/image/upload/league/apps/league-site/media-guides/2024/BAL.pdf) confirms the nickname. |
| MurrBi00 | 00-0036093 | Bill Murray | CHI participation in all three source games. Same-team roster match. |
| ShenJo00 | 00-0038920 | John Samuel Shenker | LV participation under John Shenker in all eight source games. The roster preserves the given name and the [Raiders all-time roster](https://www.raiders.com/history/all-time-roster/bios-s/john-samuel-shenker) confirms the full name and 2024 game count. |
| WhitCo05 | 00-0035891 | Cody White | SEA participation in all four 2024 and ten 2025 source games. Same-team roster match distinguishes the receiver from the historical guard. |
| WillRo08 | 00-0037451 | Rod Williams | PIT participation in all six source games. Same-team roster match at tight end and both name forms in the [Steelers media guide](https://static.clubs.nfl.com/image/upload/steelers/lw4pauak1y5f3cx3dit0.pdf). |
| CartNa00 | 00-0040547 | Nate Carter | ATL participation in all seven source games and same-team roster match at running back. Official [Falcons roster](https://www.atlantafalcons.com/news/atlanta-falcons-2026-roster) and [club game notes](https://static.clubs.nfl.com/image/upload/saints/u3s4571bromfdynsus0q.pdf) use the short and full names. |
| HallGa01 | 00-0039265 | Gabe Hall | PHI participation in both source games. Same-team roster match at defensive line. |
| JohnIs03 | 00-0039483 | Isaiah Johnson | MIA participation in all four source games. Same-team roster match at defensive back distinguishes other players with the same name. |
| JoneJa16 | 00-0040317 | Jacoby Jones | WAS participation in the source game and same-team roster match. The Nov. 25 [nflverse players release](https://github.com/nflverse/nflverse-data/releases/tag/players) also returned this ID. The pinned roster uses `JoneJa15` for the same GSIS ID. |
| MartAd00 | 00-0038658 | Adrian Martinez | SF participation in the source game and same-team roster match at quarterback. The Nov. 25 [nflverse players release](https://github.com/nflverse/nflverse-data/releases/tag/players) also returned this ID. |
| OkoyCJ00 | 00-0039176 | Basil “C.J.” Okoye | BAL participation in all 12 source games and same-team roster match at defensive line. The [Ravens biography](https://www.baltimoreravens.com/news/cj-okoye-basil-nigeria-africa-ravens-international-pathway-program-stand-out-new-reasons-training-camp) confirms the name variant. |

After rebuilding, all 26,615 snap rows in 2024 and 26,612 in 2025 matched a player ID.
All 98 formerly unmatched rows also have a participation record for the same game,
team, and GSIS ID. The supplementary players extract retrieved on Nov. 25 has SHA-256
`bf9694dd9a5769e79f76a3f431ec1953795ddd95bbec25920f4b9a226a37525f`.
Snap and participation feeds have different play definitions, so they provide separate
opportunity measures.

## 2024 cumulative EPA

The three games with an absolute cumulative gap over 0.1 EPA had a highest-ID row beyond
the explicit `END GAME` marker. Those rows contained zero row-level EPA but carried a
different cumulative value. The `END GAME` values agree with signed raw full-game EPA on
all three games to floating-point precision. The numbers below use the home team's sign.

| Game | END GAME play ID | Highest play ID | Highest-ID event | Gap in EPA |
|---|---:|---:|---|---:|
| ATL at NO, Week 10 | 4336 | 4357 | Timeout | +6.74844 |
| MIN at CHI, Week 12 | 4788 | 4808 | Timeout | +0.11169 |
| WAS at TB, Wild Card | 3839 | 3854 | Skycam wire stoppage | +2.16326 |

`make reconcile` writes the trace beside the original reconciliation report. Keep the
highest-ID cumulative comparison as a diagnostic. The team efficiency analysis uses
play-level EPA. [nflfastR field definitions](https://nflfastr.com/reference/fast_scraper.html)

## Player opportunity definitions

- A player-game includes a PFR snap row or a recorded participation appearance on an analysis
  play. Role is the game's PFR position group where available, otherwise the player dimension's
  primary position group. Season rows are split by team and role. They cover regular and
  postseason appearances and show the total completed games for the team.
- Reconstruct each team's offensive, defensive, and special-teams snap totals only when exactly
  one integer denominator is compatible with every source count and rounded percentage. In the
  game view, a missing denominator can still have a rounded PFR share marked with its source.
  Season shares divide the sum of player snaps by the sum of team snaps over games with usable
  numerators and denominators. The view shows games with raw snap data and games included in the
  share. [nflreadr snap count dictionary](https://nflreadr.nflverse.com/articles/dictionary_snap_counts.html)
- Each on-field count measures distinct recorded analysis plays for that player and team side.
  Coverage is the count with any recorded lineup alongside the eligible team-side plays during
  the player's listed games. A missing lineup can limit the count. Participation for these
  seasons is courtesy of FTN Data via nflverse under CC BY-SA 4.0.
  [nflreadr participation reference](https://nflreadr.nflverse.com/reference/load_participation.html)

## Team trends and validation

Observed weekly EPA per play includes nonspecial-teams plays with an EPA value and a pass or
rush flag. The descriptive ratings fit each regular season separately with a play-weighted ridge
regression using offense, opposing defense, and venue. The model shrinks offense and defense at
300 equivalent plays and venue at 60, then centers both team effects. Positive ratings indicate
stronger performance relative to league average on either side. The overall rating adds the two
effects. The dashboard shows 90% percentile intervals from 200 whole-game bootstrap draws.

The predictive check trains through the preceding week and evaluates each week from Weeks 5–18.
The offense-only baseline uses the same offensive and venue terms and shrinkage. The target is
matchup EPA/play, weighted by the number of eligible plays. This check does not evaluate game
outcomes.

| Season | Held-out games | Offense-only RMSE | Adjusted RMSE | Offense-only MAE | Adjusted MAE |
|---|---:|---:|---:|---:|---:|
| 2024 | 208 | 0.15128 | 0.15047 | 0.12166 | 0.12130 |
| 2025 | 208 | 0.20100 | 0.19319 | 0.15978 | 0.15482 |
