"""将 SyncPayload HTTP POST 到本仓接收端（禁止直连 PG）。"""

from __future__ import annotations

import httpx

from app.ops.admin.schema import SyncPayload

SYNC_PATH = "/api/ops/admin/sync"
# GHA 跑在海外，生产 API 在国内；60s 会在写 body 阶段超时（WriteTimeout）。
DEFAULT_POST_TIMEOUT = httpx.Timeout(connect=30.0, read=180.0, write=180.0, pool=30.0)


def payload_body_bytes(payload: SyncPayload) -> bytes:
    """序列化后的 JSON 字节；用于打日志，禁止夹带 token。"""
    return payload.model_dump_json().encode("utf-8")


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
        "Content-Type": "application/json",
    }
    raw = payload_body_bytes(payload)
    if http_client is not None:
        return http_client.post(url, content=raw, headers=headers)
    with httpx.Client(timeout=DEFAULT_POST_TIMEOUT) as client:
        return client.post(url, content=raw, headers=headers)
