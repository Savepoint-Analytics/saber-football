"""Build weekly EPA trends and regular-season opponent-adjusted efficiency."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl
from numpy.typing import NDArray

from src.compliance.attributions import Source
from src.config import settings
from src.ingestion._storage import write_parquet
from src.warehouse.core import core_metadata_path, core_output_path
from src.warehouse.snapshots import read_build_inputs

RIDGE_PLAYS = 300.0
VENUE_RIDGE_PLAYS = 60.0
BOOTSTRAP_DRAWS = 200
BOOTSTRAP_SEED = 20261125
FloatArray = NDArray[np.float64]


def team_matchups(plays: pl.DataFrame, games: pl.DataFrame) -> pl.DataFrame:
    """Aggregate eligible offense vs. defense plays to one row per matchup and game."""
    return (
        plays.filter(
            ~pl.col("special_teams_flag")
            & (pl.col("pass_flag") | pl.col("rush_flag"))
            & pl.col("epa").is_finite()
            & pl.col("posteam_id").is_not_null()
            & pl.col("defteam_id").is_not_null()
        )
        .group_by("game_id", "posteam_id", "defteam_id")
        .agg(pl.col("epa").sum().alias("epa"), pl.len().alias("plays"))
        .rename({"posteam_id": "team_id", "defteam_id": "opponent_team_id"})
        .join(
            games.filter(
                pl.col("home_score").is_not_null() & pl.col("away_score").is_not_null()
            ).select(
                "game_id", "season", "week", "season_type", "home_team_id", "neutral_site_flag"
            ),
            on="game_id",
            how="inner",
            validate="m:1",
        )
        .with_columns(
            venue=pl.when(pl.col("neutral_site_flag"))
            .then(0.0)
            .when(pl.col("team_id") == pl.col("home_team_id"))
            .then(1.0)
            .otherwise(-1.0),
            epa_per_play=pl.col("epa") / pl.col("plays"),
        )
        .sort("week", "game_id", "team_id")
    )


def weekly_trends(matchups: pl.DataFrame) -> pl.DataFrame:
    """Show observed offense and defense EPA separately over eligible plays."""
    opponent = matchups.select(
        "game_id",
        pl.col("opponent_team_id").alias("team_id"),
        pl.col("plays").alias("defensive_plays"),
        pl.col("epa").alias("epa_allowed"),
    )
    return (
        matchups.select(
            "season",
            "week",
            "season_type",
            "game_id",
            "team_id",
            "opponent_team_id",
            pl.col("plays").alias("offensive_plays"),
            pl.col("epa").alias("offensive_epa"),
            pl.col("epa_per_play").alias("offensive_epa_per_play"),
        )
        .join(opponent, on=["game_id", "team_id"], how="left", validate="1:1")
        .with_columns(
            defensive_epa_allowed_per_play=pl.col("epa_allowed") / pl.col("defensive_plays")
        )
        .sort("week", "team_id")
    )


def _design(rows: pl.DataFrame, teams: list[str]) -> FloatArray:
    index = {team: i for i, team in enumerate(teams)}
    design = np.zeros((rows.height, 2 + 2 * len(teams)))
    design[:, 0] = 1
    design[:, 1] = rows["venue"].to_numpy()
    design[np.arange(rows.height), [2 + index[team] for team in rows["team_id"]]] = 1
    design[
        np.arange(rows.height), [2 + len(teams) + index[opp] for opp in rows["opponent_team_id"]]
    ] = -1
    return design


def _fit(design: FloatArray, outcome: FloatArray, weights: FloatArray) -> FloatArray:
    penalty = np.full(design.shape[1], RIDGE_PLAYS)
    penalty[:2] = [0, VENUE_RIDGE_PLAYS]
    weighted = design.T * weights
    return np.asarray(
        np.linalg.solve(weighted @ design + np.diag(penalty), weighted @ outcome), dtype=np.float64
    )


def _ratings(coefficients: FloatArray, teams: int) -> FloatArray:
    phases = coefficients[2:].reshape(2, teams)
    phases = phases - phases.mean(axis=1, keepdims=True)
    return np.vstack([phases, phases.sum(axis=0)])


def adjusted_efficiency(rows: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fit regular-season ratings and evaluate the adjustment on later weeks."""
    regular = rows.filter(pl.col("season_type") == "REG")
    if regular.is_empty():
        raise ValueError("opponent-adjusted efficiency requires regular-season play data")
    teams = sorted(set(regular["team_id"]) | set(regular["opponent_team_id"]))
    design = _design(regular, teams)
    outcomes = regular["epa_per_play"].to_numpy()
    weights = regular["plays"].to_numpy().astype(np.float64)
    weeks = regular["week"].to_numpy()

    coefficients = _fit(design, outcomes, weights)
    ratings = _ratings(coefficients, len(teams))
    # Resample whole games so the two offenses in one game share each draw's weight.
    _, game_index = np.unique(regular["game_id"].to_numpy(), return_inverse=True)
    num_games = int(game_index.max()) + 1
    generator = np.random.default_rng(BOOTSTRAP_SEED)
    bootstrap = []
    for _ in range(BOOTSTRAP_DRAWS):
        repeated = np.bincount(generator.integers(num_games, size=num_games), minlength=num_games)
        bootstrap.append(
            _ratings(_fit(design, outcomes, weights * repeated[game_index]), len(teams))
        )
    low, high = np.quantile(np.stack(bootstrap), [0.05, 0.95], axis=0)

    season = regular["season"][0]
    table = pl.DataFrame(
        {
            "season": [season] * len(teams),
            "team_id": teams,
            **{
                f"{phase}{suffix}": matrix[i]
                for i, phase in enumerate(
                    ("offense_adjusted_epa", "defense_adjusted_epa", "net_adjusted_epa")
                )
                for suffix, matrix in (("", ratings), ("_p05", low), ("_p95", high))
            },
        }
    )
    offense = regular.group_by("team_id").agg(
        pl.col("game_id").n_unique().alias("games"),
        pl.col("plays").sum().alias("offensive_plays"),
        (pl.col("epa").sum() / pl.col("plays").sum()).alias("observed_offensive_epa_per_play"),
    )
    defense = (
        regular.group_by("opponent_team_id")
        .agg(
            pl.col("plays").sum().alias("defensive_plays"),
            (pl.col("epa").sum() / pl.col("plays").sum()).alias("observed_epa_allowed_per_play"),
        )
        .rename({"opponent_team_id": "team_id"})
    )

    predictions = []
    baseline = design[:, : 2 + len(teams)]
    for week in sorted(set(weeks[weeks >= 5])):
        train, test = weeks < week, weeks == week
        if not train.any():
            continue
        predictions.append(
            regular.filter(pl.col("week") == week)
            .select(
                "season", "week", "game_id", "team_id", "opponent_team_id", "plays", "epa_per_play"
            )
            .with_columns(
                offense_only=baseline[test]
                @ _fit(baseline[train], outcomes[train], weights[train]),
                opponent_adjusted=design[test]
                @ _fit(design[train], outcomes[train], weights[train]),
            )
        )
    validation = (
        pl.concat(predictions)
        if predictions
        else pl.DataFrame(
            schema={
                "season": pl.Int64,
                "week": pl.Int64,
                "game_id": pl.String,
                "team_id": pl.String,
                "opponent_team_id": pl.String,
                "plays": pl.UInt32,
                "epa_per_play": pl.Float64,
                "offense_only": pl.Float64,
                "opponent_adjusted": pl.Float64,
            }
        )
    )
    return (
        table.join(offense, on="team_id", how="left")
        .join(defense, on="team_id", how="left")
        .sort("net_adjusted_epa", descending=True),
        validation,
    )


def efficiency_path(table: str, season: int) -> Path:
    return (
        settings.data_dir
        / "analytics"
        / table
        / "league=nfl"
        / f"season={season}"
        / f"{table}.parquet"
    )


def efficiency_metadata_path(season: int) -> Path:
    return settings.data_dir / "analytics" / f"season={season}" / "team_efficiency_metadata.json"


def write_efficiency(season: int) -> dict[str, object]:
    matchups = team_matchups(
        pl.read_parquet(core_output_path("fact_play", season)),
        pl.read_parquet(core_output_path("dim_game", season)),
    )
    weekly = weekly_trends(matchups)
    ratings, validation = adjusted_efficiency(matchups)
    artifacts = {}
    for table, frame in (
        ("team_weekly", weekly),
        ("team_adjusted_efficiency", ratings),
        ("team_efficiency_validation", validation),
    ):
        path = efficiency_path(table, season)
        write_parquet(frame, path, sources=[Source.NFLVERSE])
        artifacts[table] = {"path": str(path), "rows": frame.height}
    scores = validation.select(
        pl.col("game_id").n_unique().alias("games"),
        pl.col("week").n_unique().alias("weeks"),
        *[
            expression
            for model in ("offense_only", "opponent_adjusted")
            for residual in (pl.col(model) - pl.col("epa_per_play"),)
            for expression in (
                (((residual**2 * pl.col("plays")).sum() / pl.col("plays").sum()).sqrt()).alias(
                    f"{model}_weighted_rmse"
                ),
                ((residual.abs() * pl.col("plays")).sum() / pl.col("plays").sum()).alias(
                    f"{model}_weighted_mae"
                ),
            )
        ],
    ).to_dicts()[0]
    if validation.is_empty():
        scores = {"games": 0, "weeks": 0}
    pins = read_build_inputs(core_metadata_path(season), season) or {}
    metadata = {
        "season": season,
        "built_at_utc": datetime.now(UTC).isoformat(),
        "claim_type": "descriptive",
        "validation_claim_type": "predictive",
        "ridge_plays": RIDGE_PLAYS,
        "venue_ridge_plays": VENUE_RIDGE_PLAYS,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "raw_inputs": {dataset: asdict(pin) for dataset, pin in pins.items()},
        "outputs": artifacts,
        "walk_forward_validation": scores,
    }
    path = efficiency_metadata_path(season)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", required=True, type=int)
    print(json.dumps(write_efficiency(parser.parse_args().season), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
