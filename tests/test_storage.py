from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from src.compliance.attributions import Source
from src.ingestion import _storage


class FakeFrame:
    def write_parquet(self, path: Path) -> None:
        path.write_bytes(b"fake parquet")


def test_split_s3_uri_requires_bucket_and_key():
    assert _storage._split_s3_uri("s3://sabermetrics/bronze/file.parquet") == (
        "sabermetrics",
        "bronze/file.parquet",
    )


def test_write_parquet_uploads_object_and_notice_for_s3_uri(monkeypatch):
    uploads: dict[tuple[str, str], tuple[bytes, str]] = {}

    def fake_put(bucket: str, key: str, body: bytes, content_type: str) -> None:
        uploads[(bucket, key)] = (body, content_type)

    monkeypatch.setattr(_storage, "_put_minio_object", fake_put)

    path = "s3://sabermetrics/football/nflverse_pbp/league=nfl/file.parquet"

    assert _storage.write_parquet(FakeFrame(), path, sources=[Source.NFLVERSE]) == path
    assert uploads[("sabermetrics", "football/nflverse_pbp/league=nfl/file.parquet")] == (
        b"fake parquet",
        "application/octet-stream",
    )

    notice_body, notice_type = uploads[
        ("sabermetrics", "football/nflverse_pbp/league=nfl/NOTICE.txt")
    ]
    assert b"Data via nflverse" in notice_body
    assert notice_type == "text/plain; charset=utf-8"


def test_minio_put_escapes_partition_keys(monkeypatch):
    connection = Mock()
    connection.getresponse.return_value = SimpleNamespace(status=200, read=lambda size: b"")
    monkeypatch.setattr(_storage.http.client, "HTTPConnection", lambda *args, **kwargs: connection)
    monkeypatch.setattr(
        _storage,
        "settings",
        SimpleNamespace(
            minio_endpoint="http://localhost:9000",
            minio_access_key="test-key",
            minio_secret_key="test-secret",
        ),
    )

    _storage._put_minio_object("football", "raw/league=nfl/file name", b"test", "text/plain")

    assert connection.request.call_args.args == ("PUT", "/football/raw/league%3Dnfl/file%20name")
    connection.close.assert_called_once()
