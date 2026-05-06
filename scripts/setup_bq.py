"""One-time setup: create the BigQuery dataset + moments table.

Idempotent — safe to re-run. Cheap and fast (no LRO, no waiting).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.vector_store import VectorStore


def main() -> None:
    cfg = Config.load()
    print(
        f"Setting up BigQuery vector store at "
        f"{cfg.project_id}.{cfg.bq_dataset}.{cfg.bq_moments_table} "
        f"(location={cfg.location}) ..."
    )
    store = VectorStore(cfg)
    store.ensure_table()
    print("Ready.")


if __name__ == "__main__":
    main()
