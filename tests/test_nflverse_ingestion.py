"""nflverse ingestion dispatch behavior that does not require network access."""

import pytest

from src.ingestion import nflverse
from src.ingestion.nflverse import DATASET_OUTPUT_NAMES, pull_dataset


def test_dataset_registry_contains_next_priority_sources():
    for dataset in ["teams", "players", "rosters", "participation", "snap_counts"]:
        assert dataset in DATASET_OUTPUT_NAMES


def test_seasonal_dataset_requires_season_before_loading():
    with pytest.raises(ValueError, match="requires --season"):
        pull_dataset("rosters")


@pytest.mark.parametrize(("season", "provider"), [(2022, "NFL Next Gen Stats"), (2025, "FTN Data")])
def test_participation_snapshot_notice_credits_season_provider(
    monkeypatch, tmp_path, season, provider
):
    import polars as pl

    path = tmp_path / "participation.parquet"
    monkeypatch.setattr(nflverse, "local_path_for_dataset", lambda *args, **kwargs: path)

    nflverse._write_dataset("participation", season, pl.DataFrame({"play_id": [1]}))

    notice = (tmp_path / "NOTICE.txt").read_text(encoding="utf-8")
    assert provider in notice
    assert "CC BY-SA 4.0" in notice
