"""Canonical football data-source attributions, centralized for export stamping."""

from __future__ import annotations

from enum import StrEnum


class Source(StrEnum):
    """Data sources whose attribution may need to appear on a deliverable."""

    NFLVERSE = "nflverse"
    NFL_NGS = "nfl_ngs"
    NFL_PARTICIPATION_NGS = "nfl_participation_ngs"
    NFL_PARTICIPATION_FTN = "nfl_participation_ftn"
    CFBD = "college_football_data"
    BIG_DATA_BOWL = "big_data_bowl"
    PFR = "pro_football_reference"
    OVER_THE_CAP = "over_the_cap"
    SPOTRAC = "spotrac"
    NFLPA = "nflpa"
    FORBES = "forbes"
    NCAA_FINANCE = "ncaa_finance"
    BETTING_LINES = "betting_lines"


ATTRIBUTIONS: dict[Source, str] = {
    Source.NFLVERSE: "Data via nflverse (nflfastR / nflreadr).",
    Source.NFL_NGS: "Includes NFL Next Gen Stats aggregates (via nflverse).",
    Source.NFL_PARTICIPATION_NGS: (
        "Participation data via NFL Next Gen Stats and nflverse (CC BY-SA 4.0)."
    ),
    Source.NFL_PARTICIPATION_FTN: "Participation data via FTN Data and nflverse (CC BY-SA 4.0).",
    Source.CFBD: "College data via CollegeFootballData.com.",
    Source.BIG_DATA_BOWL: "NFL Big Data Bowl data subject to Kaggle competition rules.",
    Source.PFR: "Stats courtesy of Pro-Football-Reference.com (Sports Reference LLC).",
    Source.OVER_THE_CAP: "Contract data via OverTheCap.",
    Source.SPOTRAC: "Contract data via Spotrac.",
    Source.NFLPA: "Cap data via the NFLPA Public Salary Cap Report.",
    Source.FORBES: "NFL team financials are Forbes estimates, not audited figures.",
    Source.NCAA_FINANCE: (
        "NCAA finance via EADA / Knight-Newhouse / USA Today; NCAA player compensation "
        "figures are estimates, not verified salaries."
    ),
    Source.BETTING_LINES: "Betting lines are used as market benchmarks/features, not truth.",
}

RESTRICTED_REDISTRIBUTION: frozenset[Source] = frozenset(
    {
        Source.NFLVERSE,
        Source.NFL_NGS,
        Source.NFL_PARTICIPATION_NGS,
        Source.NFL_PARTICIPATION_FTN,
        Source.CFBD,
        Source.BIG_DATA_BOWL,
        Source.PFR,
        Source.OVER_THE_CAP,
        Source.SPOTRAC,
        Source.BETTING_LINES,
    }
)


def attribution_for(source: Source) -> str:
    """Return the attribution string for one source."""
    return ATTRIBUTIONS[source]


def participation_source(season: int) -> Source:
    """Identify the provider of the season's nflverse participation data."""
    return Source.NFL_PARTICIPATION_FTN if season >= 2023 else Source.NFL_PARTICIPATION_NGS


def attribution_block(
    sources: list[Source] | set[Source],
    *,
    header: str = "Data sources & attribution",
) -> str:
    """Build a deduplicated, deterministically ordered attribution block."""
    seen: list[Source] = []
    for source in sources:
        if source not in seen:
            seen.append(source)
    seen.sort(key=lambda source: list(Source).index(source))

    lines = [header, "-" * len(header)]
    lines.extend(f"- {ATTRIBUTIONS[source]}" for source in seen)
    return "\n".join(lines)


def stamp_text(body: str, sources: list[Source] | set[Source]) -> str:
    """Append the attribution block to text."""
    return f"{body.rstrip()}\n\n{attribution_block(sources)}\n"
