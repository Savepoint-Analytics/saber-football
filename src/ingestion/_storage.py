"""Bronze-layer write helpers for immutable source snapshots."""

from __future__ import annotations

import hashlib
import hmac
import http.client
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeGuard
from urllib.parse import quote, urlparse

from src.compliance.attributions import Source, attribution_block
from src.config import settings

StoragePath = Path | str


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


def local_path_for_dataset(dataset: str, *, league: str, season: int | None) -> StoragePath:
    """Return the Parquet path for a raw dataset snapshot."""
    pulled_date = datetime.now(UTC).date().isoformat()
    parts = [f"league={league}"]
    if season is not None:
        parts.append(f"season={season}")
    parts.append(f"pull_date={pulled_date}")
    path = bronze_key(dataset, *parts, f"{dataset}.parquet")
    if path.startswith("s3://"):
        return path
    return Path(path)


def _is_s3_uri(path: StoragePath) -> TypeGuard[str]:
    return isinstance(path, str) and path.startswith("s3://")


def _split_s3_uri(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.strip("/"):
        raise ValueError(f"invalid S3 URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


def _s3_sibling(uri: str, filename: str) -> str:
    bucket, key = _split_s3_uri(uri)
    parent = key.rsplit("/", 1)[0]
    return f"s3://{bucket}/{parent}/{filename}"


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret: str, date_stamp: str, region: str) -> bytes:
    k_date = _sign(("AWS4" + secret).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    return _sign(_sign(k_region, "s3"), "aws4_request")


def _put_minio_object(bucket: str, key: str, body: bytes, content_type: str) -> None:
    parsed = urlparse(settings.minio_endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("MINIO_ENDPOINT must be an HTTP or HTTPS URL")

    path = quote(f"/{bucket}/{key}", safe="/")
    host = parsed.netloc
    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = "us-east-1"
    payload_hash = hashlib.sha256(body).hexdigest()
    headers = {
        "Content-Type": content_type,
        "Host": host,
        "X-Amz-Content-Sha256": payload_hash,
        "X-Amz-Date": amz_date,
    }
    canonical_headers = "".join(
        f"{name.lower()}:{headers[name]}\n" for name in sorted(headers, key=str.lower)
    )
    signed_headers = ";".join(name.lower() for name in sorted(headers, key=str.lower))
    canonical_request = "\n".join(
        ["PUT", path, "", canonical_headers, signed_headers, payload_hash]
    )
    scope = f"{date_stamp}/{region}/s3/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    signature = hmac.new(
        _signing_key(settings.minio_secret_key, date_stamp, region),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    headers["Authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={settings.minio_access_key}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    conn_cls = (
        http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    )
    conn = conn_cls(parsed.hostname, parsed.port, timeout=30)
    try:
        conn.request("PUT", path, body=body, headers=headers)
        response = conn.getresponse()
        response_body = response.read(2048).decode(errors="replace")
    finally:
        conn.close()

    if response.status >= 300:
        code = re.search(r"<Code>([^<]+)</Code>", response_body)
        detail = code.group(1) if code else response.reason
        raise RuntimeError(f"MinIO PUT failed for s3://{bucket}/{key}: {response.status} {detail}")


def write_text(path: StoragePath, body: str) -> StoragePath:
    """Write UTF-8 text locally or to MinIO."""
    if _is_s3_uri(path):
        bucket, key = _split_s3_uri(path)
        _put_minio_object(bucket, key, body.encode("utf-8"), "text/plain; charset=utf-8")
        return path

    local_path = Path(path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(body, encoding="utf-8")
    return local_path


def write_parquet(frame: Any, path: StoragePath, *, sources: list[Source]) -> StoragePath:
    """Write a pandas/polars-like frame and a sibling NOTICE.txt.

    The concrete dataframe libraries are optional at import time; this helper only
    requires that the object expose a `write_parquet` or `to_parquet` method.
    """
    if _is_s3_uri(path):
        bucket, key = _split_s3_uri(path)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / Path(key).name
            if hasattr(frame, "write_parquet"):
                frame.write_parquet(temp_path)
            elif hasattr(frame, "to_parquet"):
                frame.to_parquet(temp_path, index=False)
            else:
                raise TypeError("frame must expose write_parquet() or to_parquet()")
            _put_minio_object(bucket, key, temp_path.read_bytes(), "application/octet-stream")
        write_text(_s3_sibling(path, "NOTICE.txt"), attribution_block(sources) + "\n")
        return path

    path = Path(path)
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
    path: StoragePath,
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
