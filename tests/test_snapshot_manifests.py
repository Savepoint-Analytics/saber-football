"""Pin and replay inputs independently of new snapshots or mutated files."""

from types import SimpleNamespace

import polars as pl
import pytest

from src.warehouse import snapshots


def test_pinned_build_reads_original_snapshot_and_detects_changed_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(snapshots, "settings", SimpleNamespace(data_dir=tmp_path))
    for dataset in (*snapshots.SEASON_DATASETS, *snapshots.SHARED_DATASETS):
        parent = tmp_path / "bronze" / dataset / "league=nfl"
        if dataset in snapshots.SEASON_DATASETS:
            parent /= "season=2024"
        initial = parent / "pull_date=2026-11-20" / f"{dataset}.parquet"
        initial.parent.mkdir(parents=True)
        pl.DataFrame({"value": [1]}).write_parquet(initial)
    manifest = tmp_path / "manifest.json"
    snapshots.write_manifest(manifest, 2024)
    pins = snapshots.read_manifest(manifest, 2024)
    assert pins is not None

    initial = tmp_path / pins["nflverse_pbp"].path
    newer = initial.parent.with_name("pull_date=2026-11-21") / initial.name
    newer.parent.mkdir()
    pl.DataFrame({"value": [2]}).write_parquet(newer)
    assert snapshots.read_snapshot("nflverse_pbp", 2024)[0]["value"].item() == 2
    assert snapshots.read_snapshot("nflverse_pbp", 2024, pins)[0]["value"].item() == 1

    pl.DataFrame({"value": [3]}).write_parquet(initial)
    with pytest.raises(ValueError, match="snapshot checksum mismatch"):
        snapshots.read_snapshot("nflverse_pbp", 2024, pins)
    with pytest.raises(ValueError, match="expected 2025"):
        snapshots.read_manifest(manifest, 2025)
