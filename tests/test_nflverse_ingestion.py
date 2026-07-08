"""nflverse ingestion dispatch behavior that does not require network access."""

import pytest

from src.ingestion.nflverse import DATASET_OUTPUT_NAMES, pull_dataset


def test_dataset_registry_contains_next_priority_sources():
    for dataset in ["teams", "players", "rosters", "participation", "snap_counts"]:
        assert dataset in DATASET_OUTPUT_NAMES


def test_seasonal_dataset_requires_season_before_loading():
    with pytest.raises(ValueError, match="requires --season"):
        pull_dataset("rosters")
