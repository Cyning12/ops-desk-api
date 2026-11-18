"""lg-rag runs 只读 API（P3-T4 · 契约 15-p3-contracts.md §3）。

路由挂 ``APIRouter(prefix="/lg-rag")``，由 ``app/ops/router.py`` 注册进
``/api/ops`` → 实际路径：

- ``GET /api/ops/lg-rag/threads/{thread_id}/runs``（§3.1：thread 属主 runs
  卡片列表 · keyset 分页 · schedule 归因投影）
- ``GET /api/ops/lg-rag/runs/{run_id}/events``（§3.2：单 run 白名单事件帧流
  · 500 帧截断 · after_seq 续拉）

**import 纪律**（承 history_router · task N1 钉）：鉴权 ``CurrentUser`` 与
ORM ``OpsUser`` 经同族 ``app.ops.lg_rag.router`` 间接取；DB 访问全走
store 层（run_store / event_store / thread_store），本层零直连
``app.db.*`` / ``app.ops.deps`` → .importlinter 零改动。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.ops.lg_rag import event_store, history, run_store, thread_store
from app.ops.lg_rag.router import CurrentUser, OpsUser

router = APIRouter(prefix="/lg-rag", tags=["lg-rag-runs"])

_THREAD_ID_MAX = 255
_RUN_ID_MAX = 64
_CURSOR_MAX = 512
# §3.1（R-P3-8）：runs 列表分页默认 20 · 上限 50（超限 422）
RUNS_DEFAULT_LIMIT = 20
RUNS_MAX_LIMIT = 50
# §3.2：events 单次最多 500 帧（契约固定页幅，不对客户端暴露 limit）
EVENTS_PAGE_SIZE = 500


def _iso(value: Any) -> str | None:
    """datetime → ISO 字符串；None → None（投影字段可空）。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _query_summary(raw: str | None) -> str | None:
    """query_summary：空白归一 + 截 80（[:79]+"…" 承 history.thread_title 风格）。"""
    if not raw:
        return None
    text = " ".join(raw.split())
    if not text:
        return None
    if len(text) > history.TITLE_MAX_CHARS:
        return text[: history.TITLE_MAX_CHARS - 1] + "…"
    return text


def _map_cursor_error(exc: history.HistoryCursorError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc) or "invalid cursor")


async def _load_runs_page(
    user_id: str, thread_id: str, *, limit: int, cursor: str | None
) -> dict[str, Any]:
    """§3.1 数据装配：归属 404 + keyset 页 + query/归因批量反查（防 N+1）。"""
    owner = await thread_store.thread_owner(thread_id)
    if owner is None or str(owner) != str(user_id):
        # 跨用户/未知一律 404，不泄露存在性（承 history_router FP-1）
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    after = None
    if cursor is not None:
        try:
            after = history.runs_cursor_after(cursor)
        except history.HistoryCursorError as exc:
            raise _map_cursor_error(exc) from None
    rows = await run_store.list_thread_runs_page(user_id, thread_id, limit=limit, after=after)
    page = rows[:limit]
    run_ids = [row["run_id"] for row in page]
    queries = await run_store.fetch_run_start_queries(run_ids)
    attributions = await run_store.fetch_schedule_attributions(run_ids)
    runs = [
        {
            "run_id": row["run_id"],
            "thread_id": row["thread_id"],
            "status": row["status"],
            "created_at": _iso(row["created_at"]),
            "finished_at": _iso(row["finished_at"]),
            "query_summary": _query_summary(queries.get(row["run_id"])),
            "schedule_attribution": attributions.get(row["run_id"]),
            # P4-T6 Run 树投影加性（19 §11.4 · 加性变更豁免零 diff）
            "parent_run_id": row["parent_run_id"],
            "depth": row["depth"],
        }
        for row in page
    ]
    next_cursor = None
    if len(rows) > limit and page:
        last = page[-1]
        next_cursor = history.make_runs_cursor(last["created_at"], last["run_id"])
    return {"runs": runs, "next_cursor": next_cursor}


@router.get("/threads/{thread_id}/runs")
async def list_thread_runs(
    thread_id: str = Path(..., max_length=_THREAD_ID_MAX),
    user: OpsUser = CurrentUser,
    limit: int = Query(
        default=RUNS_DEFAULT_LIMIT,
        ge=1,
        le=RUNS_MAX_LIMIT,
        description="每页 run 数（默认 20 · 上限 50 · 超限 422）",
    ),
    cursor: str | None = Query(default=None, max_length=_CURSOR_MAX),
) -> dict[str, Any]:
    """thread 属主 runs 卡片列表（§3.1）；跨用户/未知 → 404。"""
    data = await _load_runs_page(str(user.id), thread_id, limit=limit, cursor=cursor)
    return {"ok": True, "data": data}


@router.get("/runs/{run_id}/events")
async def get_run_events(
    run_id: str = Path(..., max_length=_RUN_ID_MAX),
    user: OpsUser = CurrentUser,
    after_seq: int = Query(default=0, ge=0, description="续拉游标（只取 seq 更大帧）"),
) -> dict[str, Any]:
    """单 run 白名单事件帧流（§3.2）；跨用户/未知 → 404（assert_run_owned）。"""
    try:
        page = await event_store.list_run_events_page(
            run_id, str(user.id), after_seq=after_seq, limit=EVENTS_PAGE_SIZE
        )
    except event_store.LgRagRunNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        ) from None
    return {
        "ok": True,
        "data": {
            "run_id": run_id,
            "events": [
                {
                    "seq": ev["seq"],
                    "event_type": ev["event_type"],
                    "payload": ev["payload"],
                    "created_at": _iso(ev["created_at"]),
                }
                for ev in page["events"]
            ],
            "truncated": page["truncated"],
            "next_after_seq": page["next_after_seq"],
        },
    }
