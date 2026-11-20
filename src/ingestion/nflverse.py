"""NFL raw ingestion through nflverse-compatible Python loaders."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from src.compliance.attributions import Source, participation_source
from src.ingestion._storage import (
    StoragePath,
    local_path_for_dataset,
    metadata_for,
    write_parquet,
    write_text,
)
from src.schemas.bronze import validate_nfl_pbp_columns, validate_nfl_schedule_columns

SEASONAL_DATASETS: dict[str, str] = {
    "pbp": "load_pbp",
    "schedules": "load_schedules",
    "rosters": "load_rosters",
    "participation": "load_participation",
    "snap_counts": "load_snap_counts",
}

SNAPSHOT_DATASETS: dict[str, str] = {
    "players": "load_players",
    "teams": "load_teams",
}

DATASET_OUTPUT_NAMES: dict[str, str] = {
    "pbp": "nflverse_pbp",
    "schedules": "nflverse_schedules",
    "rosters": "nflverse_rosters",
    "participation": "nflverse_participation",
    "snap_counts": "nflverse_snap_counts",
    "players": "nflverse_players",
    "teams": "nflverse_teams",
}

DATASET_SOURCES: dict[str, list[Source]] = {
    "snap_counts": [Source.NFLVERSE, Source.PFR],
}


def _load_nflreadpy() -> Any:
    try:
        import nflreadpy as nfl
    except ImportError as exc:  # pragma: no cover - depends on optional runtime env
        raise RuntimeError(
            "nflreadpy is required for nflverse ingestion. Run `uv sync` first."
        ) from exc
    return nfl


def _call_loader(loader: Callable[..., Any], season: int) -> Any:
    """Call nflreadpy loaders across minor API signature differences."""
    try:
        return loader(seasons=[season])
    except TypeError:
        return loader([season])


def pull_pbp(season: int) -> Any:
    """Load nflverse play-by-play for a season."""
    nfl = _load_nflreadpy()
    if not hasattr(nfl, "load_pbp"):
        raise RuntimeError("Installed nflreadpy does not expose load_pbp().")
    frame = _call_loader(nfl.load_pbp, season)
    validate_nfl_pbp_columns(frame)
    return frame


def pull_schedules(season: int) -> Any:
    """Load nflverse schedules for a season."""
    nfl = _load_nflreadpy()
    if not hasattr(nfl, "load_schedules"):
        raise RuntimeError("Installed nflreadpy does not expose load_schedules().")
    frame = _call_loader(nfl.load_schedules, season)
    validate_nfl_schedule_columns(frame)
    return frame


def pull_dataset(dataset: str, season: int | None = None) -> Any:
    """Load a supported nflverse dataset."""
    nfl = _load_nflreadpy()
    if dataset in SEASONAL_DATASETS:
        if season is None:
            raise ValueError(f"{dataset} requires --season")
        loader_name = SEASONAL_DATASETS[dataset]
        if not hasattr(nfl, loader_name):
            raise RuntimeError(f"Installed nflreadpy does not expose {loader_name}().")
        frame = _call_loader(getattr(nfl, loader_name), season)
    elif dataset in SNAPSHOT_DATASETS:
        loader_name = SNAPSHOT_DATASETS[dataset]
        if not hasattr(nfl, loader_name):
            raise RuntimeError(f"Installed nflreadpy does not expose {loader_name}().")
        frame = getattr(nfl, loader_name)()
    else:
        raise ValueError(f"unsupported dataset: {dataset}")

    if dataset == "pbp":
        validate_nfl_pbp_columns(frame)
    elif dataset == "schedules":
        validate_nfl_schedule_columns(frame)
    return frame


def _write_dataset(dataset: str, season: int | None, frame: Any) -> StoragePath:
    output_name = DATASET_OUTPUT_NAMES[dataset]
    path = local_path_for_dataset(output_name, league="nfl", season=season)
    if dataset == "participation" and season is not None:
        sources = [Source.NFLVERSE, participation_source(season)]
    else:
        sources = DATASET_SOURCES.get(dataset, [Source.NFLVERSE])
    write_parquet(frame, path, sources=sources)
    metadata = metadata_for(
        dataset=output_name,
        league="nfl",
        season=season,
        source=Source.NFLVERSE,
        frame=frame,
        path=path,
    )
    metadata_path = (
        path.rsplit("/", 1)[0] + "/extract_metadata.json"
        if isinstance(path, str)
        else path.parent / "extract_metadata.json"
    )
    write_text(
        metadata_path,
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
    )
    return path


def ingest_dataset(dataset: str, season: int | None = None) -> StoragePath:
    """Pull and snapshot a supported nflverse dataset."""
    frame = pull_dataset(dataset, season)
    return _write_dataset(dataset, season, frame)


def ingest_pbp(season: int) -> StoragePath:
    """Pull and snapshot one season of nflverse play-by-play."""
    return ingest_dataset("pbp", season)


def ingest_schedules(season: int) -> StoragePath:
    """Pull and snapshot one season of nflverse schedules."""
    return ingest_dataset("schedules", season)


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: `python -m src.ingestion.nflverse pbp --season 2025`."""
    parser = argparse.ArgumentParser(description="Ingest nflverse raw datasets.")
    parser.add_argument("dataset", choices=sorted([*SEASONAL_DATASETS, *SNAPSHOT_DATASETS]))
    parser.add_argument("--season", type=int, required=False)
    args = parser.parse_args(argv)

    path = ingest_dataset(args.dataset, args.season)
    print(path)


if __name__ == "__main__":
    main()
