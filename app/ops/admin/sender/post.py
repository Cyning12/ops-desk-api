"""将 SyncPayload HTTP POST 到本仓接收端（禁止直连 PG）。"""

from __future__ import annotations

import httpx

from app.ops.admin.schema import SyncPayload

SYNC_PATH = "/api/ops/admin/sync"


def post_sync_payload(
    *,
    base_url: str,
    token: str,
    payload: SyncPayload,
    http_client: httpx.Client | None = None,
) -> httpx.Response:
    """POST SyncPayload；调用方负责检查 2xx。不记录 token。"""
    url = base_url.rstrip("/") + SYNC_PATH
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    body = payload.model_dump(mode="json")
    if http_client is not None:
        return http_client.post(url, json=body, headers=headers)
    with httpx.Client(timeout=60.0) as client:
        return client.post(url, json=body, headers=headers)
