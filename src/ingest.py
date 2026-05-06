"""End-to-end ingest: video file/URI -> Gemini moments -> embeddings -> Vector Search."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .embedder import Embedder, moment_to_text
from .extractor import MomentExtractor
from .gcs_utils import signed_clip_url, upload_video, write_json
from .vector_store import VectorStore
from .video_segmenter import probe_duration, split_segments


def ingest_video(
    cfg: Config,
    source: str,
    video_id: Optional[str] = None,
    segment_length: int = 600,
    overlap: int = 0,
    save_local: bool = True,
) -> Dict[str, Any]:
    """Ingest a single video. `source` is either a local path or a gs:// URI."""
    if source.startswith("gs://"):
        gcs_uri = source
        duration_source = signed_clip_url(cfg, gcs_uri, expires_minutes=30)
        vid = video_id or Path(source).stem
    else:
        local = Path(source)
        vid = video_id or local.stem
        duration_source = str(local)
        print(f"[ingest] uploading {local} -> gs://{cfg.gcs_bucket}/...")
        gcs_uri = upload_video(cfg, local, vid)
    print(f"[ingest] gcs_uri={gcs_uri}")

    duration = probe_duration(duration_source)
    segments = split_segments(duration, segment_length=segment_length, overlap=overlap)
    print(f"[ingest] duration={duration}s, segments={segments}")

    extractor = MomentExtractor(cfg)
    moments = extractor.extract_video(gcs_uri, segments)
    print(f"[ingest] extracted {len(moments)} moments")

    embedder = Embedder(cfg)
    texts = [moment_to_text(m) for m in moments]
    vectors = embedder.embed(texts)
    print(f"[ingest] embedded {len(vectors)} moments")

    store = VectorStore(cfg)
    ids = store.upsert(moments=moments, embeddings=vectors, video_id=vid, gcs_uri=gcs_uri)
    print(f"[ingest] upserted {len(ids)} datapoints to Vector Search")

    result = {
        "video_id": vid,
        "gcs_uri": gcs_uri,
        "duration_seconds": duration,
        "segments": segments,
        "num_moments": len(moments),
        "moment_ids": ids,
        "moments": moments,
    }

    blob_path = f"{cfg.gcs_output_prefix}/runs/{vid}.json"
    write_json(cfg, blob_path, result)
    print(f"[ingest] wrote run manifest -> gs://{cfg.gcs_bucket}/{blob_path}")

    if save_local:
        cfg.output_dir.mkdir(parents=True, exist_ok=True)
        local_out = cfg.output_dir / f"{vid}.json"
        local_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[ingest] wrote local manifest -> {local_out}")

    return result
