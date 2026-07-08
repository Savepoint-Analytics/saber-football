"""Compliance attributions must be present and stable."""

from src.compliance.attributions import (
    ATTRIBUTIONS,
    RESTRICTED_REDISTRIBUTION,
    Source,
    attribution_block,
    attribution_for,
    stamp_text,
)


def test_every_source_has_attribution():
    for source in Source:
        assert source in ATTRIBUTIONS
        assert ATTRIBUTIONS[source].strip()


def test_nflverse_notice_is_stable():
    assert attribution_for(Source.NFLVERSE) == "Data via nflverse (nflfastR / nflreadr)."


def test_block_dedupes_and_orders():
    block = attribution_block([Source.CFBD, Source.NFLVERSE, Source.CFBD])
    assert block.count("CollegeFootballData") == 1
    assert block.count("nflverse") == 1
    assert block.index("nflverse") < block.index("CollegeFootballData")


def test_stamp_text_appends_notice():
    out = stamp_text("Some analysis.", [Source.NFLPA])
    assert out.startswith("Some analysis.")
    assert "NFLPA Public Salary Cap Report" in out


def test_restricted_sources_flagged():
    assert Source.NFLVERSE in RESTRICTED_REDISTRIBUTION
    assert Source.CFBD in RESTRICTED_REDISTRIBUTION
    assert Source.NFLPA not in RESTRICTED_REDISTRIBUTION
