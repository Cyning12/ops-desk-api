"""Admin endpoint：ops_memory_facts 按 (tenant,user) 物理删除（合规删除权）。

**首个 admin 面不可逆写端点**——双闸门 + 审计断言为本端点核心否决面：

- 鉴权：`AdminSyncAuth`（Bearer `OPS_ADMIN_SYNC_TOKEN` 或 cookie maintainer ·
  零新鉴权面 · 未授权一律 401/403 且表行零变化）。
- ① **默认干跑**：`dry_run` 缺省/显式 true → 只读计数报告**零写**，响应 echo
  `dry_run` 标志（盲发只读面）。
- ② **实删须范围确认**：`dry_run=false` 时 `expected_count` 必填（缺 → 400 零删除），
  与同谓词当前匹配计数**不等 → 409 零删除**（调用方重新干跑）；计数等 → 200 实删
  且 `deleted == expected_count`。「删多少」是显式对账不是盲发。
- 审计：service 层 `logger.info` 记动作不记内容（无 key/value · 无 PII 泄漏面）。
- 500 不静默：异常 rollback + `logger.exception` + HTTPException（admin/sync.py
  :35-45 先例同形）。

残余风险（承 SPEC §7 如实承认）：expected_count 只锁数量不锁主体（计数碰巧相等
的错目标不可防 · 管理面人工纪律兜底：先干跑核对计数再实删）；同计数内容替换
竞态不可区分（管理面低频操作可接受）。
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import uuid as _uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsMemoryEpisode, OpsMemoryFact, OpsUser, now_utc
from app.db.session import get_db
from app.ops.deps import AdminSyncAuth
from app.ops.memory.service import PurgeReport, purge_by_user, revoke_by_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/memory", tags=["admin"])


class MemoryPurgePayload(BaseModel):
    """purge 请求体：tenant/user 显式传入但只在 AdminSyncAuth 通过后生效
    （admin/capability.py「替别人看一眼」先例同形态）。"""

    tenant_id: str
    user_id: str
    #: 默认干跑（盲发只读）；实删必须显式 false + expected_count 双闸门
    dry_run: bool = True
    #: 实删必填：与当前匹配计数一致才执行（先干跑取计数再提交）
    expected_count: int | None = Field(default=None, ge=0)


class MemoryPurgeResponse(BaseModel):
    """PurgeReport JSON 面（echo dry_run 标志 · by_status 分桶计数）。"""

    dry_run: bool
    scanned: int
    deleted: int
    by_status: dict[str, int]
    elapsed_s: float
    recorded_at: datetime


def _to_response(report: PurgeReport) -> MemoryPurgeResponse:
    return MemoryPurgeResponse(
        dry_run=report.dry_run,
        scanned=report.scanned,
        deleted=report.deleted,
        by_status=report.by_status,
        elapsed_s=report.elapsed_s,
        recorded_at=report.recorded_at,
    )


@router.post("/purge", response_model=MemoryPurgeResponse)
async def purge_memory(
    payload: MemoryPurgePayload,
    db: AsyncSession = Depends(get_db),
    _user: OpsUser | None = AdminSyncAuth,
) -> MemoryPurgeResponse:
    """按 (tenant,user) 物理删除：默认干跑 + expected_count 双闸门。"""
    tenant_id = payload.tenant_id.strip()
    user_id = payload.user_id.strip()
    if not tenant_id or not user_id:
        # strip 后空 = 400（service.py write_fact :110-115 strip 先例对齐）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id/user_id 空白（strip 后为空）",
        )
    if not payload.dry_run and payload.expected_count is None:
        # 双闸门②前置：缺 expected_count → 400 零删除（不触库）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="dry_run=false 必须携带 expected_count（先干跑取计数再实删）",
        )
    try:
        if payload.dry_run:
            report = await purge_by_user(tenant_id, user_id, dry_run=True, session=db)
            return _to_response(report)
        # 双闸门②：同谓词当前计数 != expected_count → 409 零删除（调用方重新干跑）
        probe = await purge_by_user(tenant_id, user_id, dry_run=True, session=db)
        if probe.scanned != payload.expected_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "reason": "count_mismatch",
                    "expected_count": payload.expected_count,
                    "current_count": probe.scanned,
                },
            )
        report = await purge_by_user(tenant_id, user_id, dry_run=False, session=db)
        await db.commit()
        return _to_response(report)
    except HTTPException:
        raise
    except Exception as exc:
        # 500 不静默：rollback + logger.exception + HTTPException（admin/sync.py 先例）
        await db.rollback()
        logger.exception("Admin memory purge failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stage": "memory_purge", "message": str(exc)},
        ) from exc


# ---------------------------------------------------------------------------
# P3-T5 admin memory 浏览/撤销端点（治理线 · 契约真源 15-p3-contracts.md §5）
#
# - admin 面=跨租户运维面：tenant_id/user_id 显式传入（不取 auth 主体），
#   只在 AdminSyncAuth（Bearer 或 maintainer cookie）通过后生效。
# - facts 分页浏览（只读投影不含 embedding · keyset 游标）+ {key} 撤销
#   （复用 service.py revoke_by_key 语义只动 active 行 · 幂等 200 affected=0）。
# - episodes 只读分页（单条 revoke 不做 · N2 登记）。
# ---------------------------------------------------------------------------

#: 词表钉死（契约 §5.2/§5.4；词表外一律 422 不查询）
_FACT_STATUS_VOCAB = frozenset({"active", "superseded", "revoked", "expired"})
_FACT_KIND_VOCAB = frozenset({"fact", "preference"})
_EPISODE_STATUS_VOCAB = frozenset({"active", "revoked"})
_EPISODE_OUTCOME_VOCAB = frozenset({"success", "failure", "partial"})


class MemoryRevokePayload(BaseModel):
    """revoke 请求体：tenant_id 必填 · user_id 可选（缺省 = tenant 全撤慎用）。

    显式空白 user_id（strip 后空）→ 400：防「慎用全撤」被笔误盲发
    （purge :84 strip 先例对齐）。
    """

    tenant_id: str
    user_id: str | None = None


class _CursorError(ValueError):
    """分页 cursor 非法；HTTP 映射 422（lg_rag HistoryCursorError 同形）。"""


# --- keyset cursor（本地最小复刻 lg_rag/history.py :41-80 形态：base64url
# JSON rstrip("=") · 坏形一律 422。admin-outbound import-linter 契约 forbidden
# 含 app.ops.lg_rag → 不可复用 → 本地复刻保 .importlinter 零改动）


def _dt_iso(value: object) -> str:
    """datetime → ISO 字符串；非 datetime 原样 str（history._dt_iso 同形）。"""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")


def _iso_or_none(value: datetime | None) -> str | None:
    return _dt_iso(value) if value is not None else None


def _encode_cursor(created_at: datetime, row_id: object) -> str:
    payload = {"ts": _dt_iso(created_at), "id": str(row_id)}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, _uuid.UUID]:
    """base64url JSON {ts,id} → (created_at, uuid)；任何坏形一律 _CursorError。"""
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        ts = datetime.fromisoformat(payload["ts"])
        rid = _uuid.UUID(str(payload["id"]))
    except (binascii.Error, KeyError, TypeError, ValueError) as exc:
        raise _CursorError(f"cursor invalid: {exc}") from exc
    return ts, rid


def _blank_400(field: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{field} 空白（strip 后为空）",
    )


def _vocab_or_422(name: str, value: str, vocab: frozenset[str]) -> str:
    if value not in vocab:
        raise HTTPException(
            status_code=422,
            detail=f"{name} 词表外：{value!r}（允许：{sorted(vocab)}）",
        )
    return value


def _keyset_condition(created_col, id_col, cursor: str | None):
    """(created_at DESC, id DESC) keyset 谓词；坏 cursor → 422。"""
    if not cursor:
        return None
    try:
        cur_ts, cur_id = _decode_cursor(cursor)
    except _CursorError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return or_(created_col < cur_ts, and_(created_col == cur_ts, id_col < cur_id))


def _fact_view(row) -> dict:
    """契约 §5.2 投影：十二字段 · 不含 embedding。"""
    return {
        "id": str(row.id),
        "tenant_id": row.tenant_id,
        "user_id": row.user_id,
        "key": row.key,
        "value": row.value,
        "kind": row.kind,
        "source_run_id": row.source_run_id,
        "source_turn": row.source_turn,
        "status": row.status,
        "expires_at": _iso_or_none(row.expires_at),
        "created_at": _dt_iso(row.created_at),
        "updated_at": _dt_iso(row.updated_at),
    }


def _episode_view(row) -> dict:
    """契约 §5.4 投影：十一字段（episodes 无 updated_at）。"""
    return {
        "id": str(row.id),
        "tenant_id": row.tenant_id,
        "run_id": row.run_id,
        "task_domain": row.task_domain,
        "context_fingerprint": row.context_fingerprint,
        "plan_summary": row.plan_summary,
        "tool_sequence": row.tool_sequence,
        "outcome": row.outcome,
        "failure_class": row.failure_class,
        "status": row.status,
        "created_at": _dt_iso(row.created_at),
    }


@router.get("/facts")
async def list_memory_facts(
    tenant_id: str = Query(..., max_length=255),
    user_id: str | None = Query(default=None, max_length=255),
    fact_status: str = Query(default="active", alias="status", max_length=16),
    kind: str | None = Query(default=None, max_length=16),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None, max_length=512),
    db: AsyncSession = Depends(get_db),
    _user: OpsUser | None = AdminSyncAuth,
) -> dict:
    """facts 分页浏览（只读 · keyset limit+1 探测 · 响应壳 {"ok","data"}）。"""
    tenant_id = tenant_id.strip()
    if not tenant_id:
        raise _blank_400("tenant_id")
    if user_id is not None:
        user_id = user_id.strip() or None
    fact_status = _vocab_or_422("status", fact_status, _FACT_STATUS_VOCAB)
    conditions = [
        OpsMemoryFact.tenant_id == tenant_id,
        OpsMemoryFact.status == fact_status,
    ]
    if user_id is not None:
        conditions.append(OpsMemoryFact.user_id == user_id)
    if kind is not None:
        kind = _vocab_or_422("kind", kind, _FACT_KIND_VOCAB)
        conditions.append(OpsMemoryFact.kind == kind)
    page_cond = _keyset_condition(OpsMemoryFact.created_at, OpsMemoryFact.id, cursor)
    if page_cond is not None:
        conditions.append(page_cond)
    stmt = (
        select(
            OpsMemoryFact.id,
            OpsMemoryFact.tenant_id,
            OpsMemoryFact.user_id,
            OpsMemoryFact.key,
            OpsMemoryFact.value,
            OpsMemoryFact.kind,
            OpsMemoryFact.source_run_id,
            OpsMemoryFact.source_turn,
            OpsMemoryFact.status,
            OpsMemoryFact.expires_at,
            OpsMemoryFact.created_at,
            OpsMemoryFact.updated_at,
        )
        .where(*conditions)
        .order_by(OpsMemoryFact.created_at.desc(), OpsMemoryFact.id.desc())
        .limit(limit + 1)
    )
    try:
        rows = (await db.execute(stmt)).all()
    except Exception as exc:
        await db.rollback()
        logger.exception("Admin memory facts list failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stage": "memory_facts_list", "message": str(exc)},
        ) from exc
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = (
        _encode_cursor(page[-1].created_at, page[-1].id) if has_more and page else None
    )
    return {
        "ok": True,
        "data": {"facts": [_fact_view(r) for r in page], "next_cursor": next_cursor},
    }


@router.post("/facts/{key}/revoke")
async def revoke_memory_fact(
    payload: MemoryRevokePayload,
    key: str = Path(..., max_length=255),
    db: AsyncSession = Depends(get_db),
    _user: OpsUser | None = AdminSyncAuth,
) -> dict:
    """按 (tenant,[user],key) 逻辑撤销：幂等 200 affected=0 否 409（契约 §5.3）。

    user_id 给定 → 直调 service.revoke_by_key（最小改动零签名变更）；缺省 →
    tenant 全撤慎用面：admin 层手写同形 UPDATE（同谓词只动 active 行 + 同审计
    形态），幂等性同质。
    """
    tenant_id = payload.tenant_id.strip()
    key = key.strip()
    if not tenant_id:
        raise _blank_400("tenant_id")
    if not key:
        raise _blank_400("key")
    user_id = payload.user_id
    if user_id is not None:
        user_id = user_id.strip()
        if not user_id:
            # 显式空白 ≠ 缺省：防「慎用全撤」被笔误盲发
            raise _blank_400("user_id")
    try:
        if user_id is not None:
            affected = await revoke_by_key(tenant_id, user_id, key, session=db)
        else:
            stmt = (
                update(OpsMemoryFact)
                .where(
                    OpsMemoryFact.tenant_id == tenant_id,
                    OpsMemoryFact.key == key,
                    OpsMemoryFact.status == "active",
                )
                .values(status="revoked", updated_at=now_utc())
            )
            result = await db.execute(stmt)
            affected = int(result.rowcount or 0)
            # 审计：记动作不记内容（key/tenant/affected · 无 value 无 PII）
            logger.info(
                "memory admin revoke_by_key key=%s tenant=%s affected=%d scope=tenant",
                key,
                tenant_id,
                affected,
            )
        await db.commit()
        return {"ok": True, "data": {"affected": affected}}
    except HTTPException:
        raise
    except Exception as exc:
        # 500 不静默：rollback + logger.exception + HTTPException（purge 先例）
        await db.rollback()
        logger.exception("Admin memory revoke failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stage": "memory_revoke", "message": str(exc)},
        ) from exc


@router.get("/episodes")
async def list_memory_episodes(
    tenant_id: str = Query(..., max_length=255),
    run_id: str | None = Query(default=None, max_length=255),
    episode_status: str | None = Query(default=None, alias="status", max_length=16),
    outcome: str | None = Query(default=None, max_length=16),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None, max_length=512),
    db: AsyncSession = Depends(get_db),
    _user: OpsUser | None = AdminSyncAuth,
) -> dict:
    """episodes 只读分页（单条 revoke 不做 · N2；写动词一律 405/404）。"""
    tenant_id = tenant_id.strip()
    if not tenant_id:
        raise _blank_400("tenant_id")
    if run_id is not None:
        run_id = run_id.strip() or None
    conditions = [OpsMemoryEpisode.tenant_id == tenant_id]
    if run_id is not None:
        conditions.append(OpsMemoryEpisode.run_id == run_id)
    if episode_status is not None:
        episode_status = _vocab_or_422("status", episode_status, _EPISODE_STATUS_VOCAB)
        conditions.append(OpsMemoryEpisode.status == episode_status)
    if outcome is not None:
        outcome = _vocab_or_422("outcome", outcome, _EPISODE_OUTCOME_VOCAB)
        conditions.append(OpsMemoryEpisode.outcome == outcome)
    page_cond = _keyset_condition(
        OpsMemoryEpisode.created_at, OpsMemoryEpisode.id, cursor
    )
    if page_cond is not None:
        conditions.append(page_cond)
    stmt = (
        select(
            OpsMemoryEpisode.id,
            OpsMemoryEpisode.tenant_id,
            OpsMemoryEpisode.run_id,
            OpsMemoryEpisode.task_domain,
            OpsMemoryEpisode.context_fingerprint,
            OpsMemoryEpisode.plan_summary,
            OpsMemoryEpisode.tool_sequence,
            OpsMemoryEpisode.outcome,
            OpsMemoryEpisode.failure_class,
            OpsMemoryEpisode.status,
            OpsMemoryEpisode.created_at,
        )
        .where(*conditions)
        .order_by(OpsMemoryEpisode.created_at.desc(), OpsMemoryEpisode.id.desc())
        .limit(limit + 1)
    )
    try:
        rows = (await db.execute(stmt)).all()
    except Exception as exc:
        await db.rollback()
        logger.exception("Admin memory episodes list failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stage": "memory_episodes_list", "message": str(exc)},
        ) from exc
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = (
        _encode_cursor(page[-1].created_at, page[-1].id) if has_more and page else None
    )
    return {
        "ok": True,
        "data": {
            "episodes": [_episode_view(r) for r in page],
            "next_cursor": next_cursor,
        },
    }
