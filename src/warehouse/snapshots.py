"""Select and verify the raw inputs for a reproducible NFL season build."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

import polars as pl
from pyarrow import fs

from src.config import settings

SEASON_DATASETS = (
    "nflverse_schedules",
    "nflverse_pbp",
    "nflverse_rosters",
    "nflverse_snap_counts",
    "nflverse_participation",
)
SHARED_DATASETS = ("nflverse_players", "nflverse_teams")


@dataclass(frozen=True)
class Snapshot:
    """Location and SHA-256 of the exact bytes consumed by a build."""

    path: str
    sha256: str


@lru_cache(maxsize=1)
def _minio() -> fs.S3FileSystem:
    endpoint = urlsplit(settings.minio_endpoint)
    if endpoint.scheme not in {"http", "https"} or not endpoint.hostname:
        raise ValueError("MINIO_ENDPOINT must be an HTTP or HTTPS URL")
    return fs.S3FileSystem(
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        region="us-east-1",
        scheme=endpoint.scheme,
        endpoint_override=endpoint.netloc,
        connect_timeout=5,
        request_timeout=30,
    )


def _latest_location(dataset: str, season: int | None, *, from_minio: bool = False) -> str:
    partition = f"{dataset}/league=nfl"
    if season is not None:
        partition += f"/season={season}"
    if from_minio:
        root = "/".join(filter(None, [settings.minio_bucket, settings.minio_prefix, partition]))
        files = _minio().get_file_info(fs.FileSelector(root, recursive=True, allow_not_found=True))
        locations = [
            f"s3://{item.path}"
            for item in files
            if item.is_file
            and Path(item.path).name == f"{dataset}.parquet"
            and Path(item.path).parent.name.startswith("pull_date=")
        ]
    else:
        root = f"bronze/{partition}"
        locations = [
            path.relative_to(settings.data_dir).as_posix()
            for path in (settings.data_dir / root).glob(f"pull_date=*/{dataset}.parquet")
        ]
    if not locations:
        raise FileNotFoundError(f"no {dataset} snapshot found under {root}")
    return max(locations)


def _read_bytes(location: str) -> bytes:
    if location.startswith("s3://"):
        with _minio().open_input_file(location.removeprefix("s3://")) as source:
            return bytes(source.read())
    return (settings.data_dir / location).read_bytes()


def _fingerprint(location: str, contents: bytes) -> Snapshot:
    return Snapshot(path=location, sha256=sha256(contents).hexdigest())


def read_snapshot(
    dataset: str, season: int | None, pins: dict[str, Snapshot] | None = None
) -> tuple[pl.DataFrame, Snapshot]:
    """Read local latest or verify and read a pinned local or MinIO snapshot."""
    expected = pins[dataset] if pins is not None else None
    location = expected.path if expected else _latest_location(dataset, season)
    contents = _read_bytes(location)
    actual = _fingerprint(location, contents)
    if expected is not None and actual.sha256 != expected.sha256:
        raise ValueError(f"snapshot checksum mismatch for {dataset} at {location}")
    return pl.read_parquet(BytesIO(contents)), actual


def read_manifest(path: Path | None, season: int) -> dict[str, Snapshot] | None:
    """Load a season manifest or raw inputs stored in build metadata."""
    if path is None:
        return None
    if not path.is_file():
        raise FileNotFoundError(path)
    pins = read_build_inputs(path, season)
    if pins is None:
        raise ValueError(f"{path} does not contain raw input pins")
    return pins


def read_build_inputs(path: Path, season: int) -> dict[str, Snapshot] | None:
    """Read provenance from a build receipt, including compatibility with legacy receipts."""
    if not path.exists():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if "raw_inputs" not in document:
        return None
    if document["season"] != season:
        raise ValueError(f"{path} was created for season {document['season']}, expected {season}")
    return {dataset: Snapshot(**item) for dataset, item in document["raw_inputs"].items()}


def write_manifest(path: Path, season: int, *, from_minio: bool = False) -> None:
    inputs = {}
    for dataset in (*SEASON_DATASETS, *SHARED_DATASETS):
        location = _latest_location(
            dataset, season if dataset in SEASON_DATASETS else None, from_minio=from_minio
        )
        inputs[dataset] = asdict(_fingerprint(location, _read_bytes(location)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"season": season, "raw_inputs": inputs}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--from-minio", action="store_true")
    args = parser.parse_args(argv)
    write_manifest(args.output, args.season, from_minio=args.from_minio)
    print(args.output)


if __name__ == "__main__":
    main()
