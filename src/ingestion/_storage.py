"""Bronze-layer write helpers for immutable source snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.compliance.attributions import Source, attribution_block
from src.config import settings


@dataclass(frozen=True)
class ExtractMetadata:
    """Metadata that should travel with every raw extract."""

    dataset: str
    league: str
    season: int | None
    source: Source
    pulled_at_utc: str
    row_count: int
    path: str


def bronze_key(dataset: str, *parts: str) -> str:
    """Compose a partitioned key under the bronze root for a dataset."""
    suffix = "/".join([dataset, *parts])
    root = settings.bronze_root
    sep = "" if root.endswith("/") else "/"
    return f"{root}{sep}{suffix}"


def local_path_for_dataset(dataset: str, *, league: str, season: int | None) -> Path:
    """Return the local Parquet path for a raw dataset snapshot."""
    pulled_date = datetime.now(UTC).date().isoformat()
    parts = [f"league={league}"]
    if season is not None:
        parts.append(f"season={season}")
    parts.append(f"pull_date={pulled_date}")
    return Path(bronze_key(dataset, *parts, f"{dataset}.parquet"))


def write_parquet(frame: Any, path: Path, *, sources: list[Source]) -> Path:
    """Write a pandas/polars-like frame and a sibling NOTICE.txt.

    The concrete dataframe libraries are optional at import time; this helper only
    requires that the object expose a `write_parquet` or `to_parquet` method.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(frame, "write_parquet"):
        frame.write_parquet(path)
    elif hasattr(frame, "to_parquet"):
        frame.to_parquet(path, index=False)
    else:
        raise TypeError("frame must expose write_parquet() or to_parquet()")

    (path.parent / "NOTICE.txt").write_text(attribution_block(sources) + "\n", encoding="utf-8")
    return path


def row_count(frame: Any) -> int:
    """Return row count for a pandas/polars-like frame."""
    if hasattr(frame, "height"):
        return int(frame.height)
    if hasattr(frame, "__len__"):
        return len(frame)
    raise TypeError("cannot determine row count")


def metadata_for(
    *,
    dataset: str,
    league: str,
    season: int | None,
    source: Source,
    frame: Any,
    path: Path,
) -> ExtractMetadata:
    """Build standard extract metadata after a successful write."""
    return ExtractMetadata(
        dataset=dataset,
        league=league,
        season=season,
        source=source,
        pulled_at_utc=datetime.now(UTC).isoformat(),
        row_count=row_count(frame),
        path=str(path),
    )
