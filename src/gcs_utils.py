"""Cloud Storage helpers: upload videos, generate signed URLs, write JSON."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from google.cloud import storage

from .config import Config


def _client(cfg: Config) -> storage.Client:
    return storage.Client(project=cfg.project_id)


def upload_video(cfg: Config, local_path: str | Path, video_id: str | None = None) -> str:
    local = Path(local_path)
    if not local.exists():
        raise FileNotFoundError(local)
    vid = video_id or local.stem
    blob_name = f"{cfg.gcs_video_prefix}/{vid}{local.suffix}"
    bucket = _client(cfg).bucket(cfg.gcs_bucket)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(local))
    return f"gs://{cfg.gcs_bucket}/{blob_name}"


def write_json(cfg: Config, blob_path: str, payload: dict) -> str:
    bucket = _client(cfg).bucket(cfg.gcs_bucket)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(
        json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    return f"gs://{cfg.gcs_bucket}/{blob_path}"


def signed_clip_url(
    cfg: Config,
    gcs_uri: str,
    start_seconds: int | None = None,
    end_seconds: int | None = None,
    expires_minutes: int = 60,
) -> str:
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"expected gs:// URI, got {gcs_uri}")
    bucket_name, _, blob_name = gcs_uri[len("gs://") :].partition("/")
    bucket = _client(cfg).bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=dt.timedelta(minutes=expires_minutes),
        method="GET",
    )
    if start_seconds is not None and end_seconds is not None:
        url = f"{url}#t={start_seconds},{end_seconds}"
    return url


def gcs_to_https(gcs_uri: str) -> str:
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"expected gs:// URI, got {gcs_uri}")
    return "https://storage.googleapis.com/" + gcs_uri[len("gs://") :]
