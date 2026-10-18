"""Qdrant 影子写：PG commit 之后非阻塞入队；失败进 DLQ，绝不回滚/阻塞 ingest。"""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings
from app.ops.rag.backend import qdrant_api_key, qdrant_collection, qdrant_url

logger = logging.getLogger(__name__)

_SHADOW_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="qdrant-shadow")
_sync_engine: Engine | None = None

# 测试可替换
_enqueue_hook: Any = None


def shadow_write_enabled() -> bool:
    return os.getenv("RAG_QDRANT_SHADOW_WRITE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


@dataclass(frozen=True)
class ShadowPoint:
    point_id: int
    vector: list[float]
    payload: dict[str, Any]


def set_enqueue_hook(hook: Any) -> None:
    """单测注入：捕获 enqueue 调用。"""
    global _enqueue_hook
    _enqueue_hook = hook


def _get_sync_engine() -> Engine:
    global _sync_engine
    if _sync_engine is None:
        sync_url = settings.database_url.replace("+asyncpg", "+psycopg")
        _sync_engine = create_engine(sync_url, pool_pre_ping=True)
    return _sync_engine


def filter_payload(
    *,
    source_type: str,
    repo: str,
    source_id: str,
    chunk_index: int,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Qdrant 仅允许 filter 字段。tenant_id 缺省试点 A。"""
    from app.ops.tenant_context import TENANT_A

    return {
        "source_type": source_type,
        "repo": repo,
        "source_id": source_id,
        "chunk_index": chunk_index,
        "tenant_id": (tenant_id or TENANT_A).strip() or TENANT_A,
    }


def enqueue_shadow_upsert(points: list[ShadowPoint]) -> None:
    """PG commit 之后调用；吞掉所有异常。"""
    if not points or not shadow_write_enabled():
        return
    if _enqueue_hook is not None:
        try:
            _enqueue_hook("upsert", points)
        except Exception:
            logger.exception("shadow enqueue hook failed op=upsert")
        return
    try:
        _SHADOW_EXECUTOR.submit(_shadow_upsert_safe, list(points))
    except Exception:
        logger.exception("enqueue shadow upsert failed n=%s", len(points))
        _write_dlq("upsert", [p.point_id for p in points], points, "enqueue_failed")


def enqueue_shadow_delete(point_ids: list[int]) -> None:
    """整组替换/墓碑删除后入队删点。"""
    ids = [int(i) for i in point_ids if i is not None]
    if not ids or not shadow_write_enabled():
        return
    if _enqueue_hook is not None:
        try:
            _enqueue_hook("delete", ids)
        except Exception:
            logger.exception("shadow enqueue hook failed op=delete")
        return
    try:
        _SHADOW_EXECUTOR.submit(_shadow_delete_safe, ids)
    except Exception:
        logger.exception("enqueue shadow delete failed n=%s", len(ids))
        _write_dlq("delete", ids, None, "enqueue_failed")


def _shadow_upsert_safe(points: list[ShadowPoint]) -> None:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qm

        client = QdrantClient(url=qdrant_url(), api_key=qdrant_api_key())
        client.upsert(
            collection_name=qdrant_collection(),
            points=[
                qm.PointStruct(
                    id=p.point_id,
                    vector=p.vector,
                    payload=p.payload,
                )
                for p in points
            ],
            wait=True,
        )
    except Exception as exc:
        logger.exception("shadow upsert failed n=%s", len(points))
        _write_dlq("upsert", [p.point_id for p in points], points, str(exc))


def _shadow_delete_safe(point_ids: list[int]) -> None:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qm

        client = QdrantClient(url=qdrant_url(), api_key=qdrant_api_key())
        client.delete(
            collection_name=qdrant_collection(),
            points_selector=qm.PointIdsList(points=point_ids),
            wait=True,
        )
    except Exception as exc:
        logger.exception("shadow delete failed n=%s", len(point_ids))
        _write_dlq("delete", point_ids, None, str(exc))


def _write_dlq(
    op: str,
    point_ids: list[int],
    points: list[ShadowPoint] | None,
    error: str,
) -> None:
    payload: dict[str, Any] | None = None
    if points:
        payload = {
            "points": [
                {
                    "id": p.point_id,
                    "vector": p.vector,
                    "payload": p.payload,
                }
                for p in points
            ]
        }
    try:
        engine = _get_sync_engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO ops_qdrant_dlq (op, point_ids, payload, error) "
                    "VALUES (:op, CAST(:ids AS jsonb), CAST(:payload AS jsonb), :error)"
                ),
                {
                    "op": op,
                    "ids": json.dumps(point_ids),
                    "payload": json.dumps(payload) if payload is not None else None,
                    "error": error[:4000],
                },
            )
    except Exception:
        logger.exception("write ops_qdrant_dlq failed op=%s ids=%s", op, point_ids[:20])
