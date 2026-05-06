"""One-off: tear down Vertex AI Vector Search resources from an earlier setup.

Cancels any in-progress deploy LRO on the endpoint, then deletes the index
endpoint (force=True undeploys first) and the index. Idempotent — re-running
on already-deleted resources is fine.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.api_core import exceptions as gax_exceptions
from google.cloud import aiplatform, aiplatform_v1

from src.config import Config

INDEX_DISPLAY_NAME = "video-moments-rag-index"
ENDPOINT_DISPLAY_NAME = f"{INDEX_DISPLAY_NAME}-endpoint"


def _cancel_running_ops_on_endpoint(cfg: Config, endpoint_resource_name: str) -> None:
    api_endpoint = f"{cfg.location}-aiplatform.googleapis.com"
    ep_client = aiplatform_v1.IndexEndpointServiceClient(
        client_options={"api_endpoint": api_endpoint}
    )
    op_client = ep_client._transport.operations_client
    try:
        ops = op_client.list_operations(name=endpoint_resource_name, filter_="done=false")
        for op in ops:
            print(f"  cancelling operation: {op.name}")
            try:
                op_client.cancel_operation(name=op.name)
            except gax_exceptions.GoogleAPIError as e:
                print(f"    cancel failed: {e}")
    except gax_exceptions.GoogleAPIError as e:
        print(f"  (could not list ops, continuing): {e}")


def main() -> None:
    cfg = Config.load()
    aiplatform.init(project=cfg.project_id, location=cfg.location)

    endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
        filter=f'display_name="{ENDPOINT_DISPLAY_NAME}"'
    )
    for ep in endpoints:
        print(f"Endpoint: {ep.resource_name}")
        _cancel_running_ops_on_endpoint(cfg, ep.resource_name)
        print("  deleting (force=True undeploys any deployed indexes first)...")
        try:
            ep.delete(force=True, sync=True)
            print("  deleted")
        except gax_exceptions.GoogleAPIError as e:
            print(f"  delete failed: {e}")
            print("  --> the deploy may still be in progress; wait a minute and re-run.")

    indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{INDEX_DISPLAY_NAME}"')
    for idx in indexes:
        print(f"Index: {idx.resource_name}")
        try:
            idx.delete(sync=True)
            print("  deleted")
        except gax_exceptions.GoogleAPIError as e:
            print(f"  delete failed: {e}")

    print("Cleanup complete.")


if __name__ == "__main__":
    main()
