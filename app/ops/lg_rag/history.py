"""lg-rag 会话历史聚合纯函数（chat-history-api B1 · H3）。

输入 = ``event_store`` 拉出的**事件行 dict**（``run_id/seq/event_type/payload/
created_at`` 等键），输出 = threads 列表摘要 / 单 thread 消息视图。
**不碰 DB**、不 import session/models——全部可单测。

裁定锚点：
- A1：``run.start`` payload 增**可选** ``query`` 键；存量旧 run 无该键 →
  FP-4 标题降级（run_id 前缀 + 时间），列表不阻塞。
- N3：单 run answer 聚合超 ``ANSWER_MAX_CHARS`` 截断并标 ``answer_truncated``。
- Q1：真源只有事件表——这里只认事件行，绝不读 checkpoint / turns。
"""
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any

# N3 钉：单 run answer 聚合上限（字符）；超出截断 + answer_truncated=true
ANSWER_MAX_CHARS = 32_000
# 列表标题上限（字符）；query 即标题真源，超长截断
TITLE_MAX_CHARS = 80
# H1 列表 / H2 历史分页默认与上限（history_router Query 校验同源真值）
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

_EVENT_RUN_START = "run.start"
_EVENT_ANSWER = "answer"
_EVENT_SUBTASK_PROGRESS = "subtask.progress"
_EVENT_HITL_WAITING = "hitl.waiting"
_EVENT_DONE = "done"
_EVENT_ERROR = "error"


class HistoryCursorError(ValueError):
    """历史分页 cursor 非法；HTTP 映射 422。"""


def _dt_iso(value: Any) -> str:
    """datetime → ISO 字符串；非 datetime（缺列兜底）原样 str。"""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")


def _parse_dt(raw: str) -> datetime:
    """ISO 字符串 → datetime；非法抛 ``HistoryCursorError``。"""
    try:
        return datetime.fromisoformat(raw)
    except (TypeError, ValueError) as exc:
        raise HistoryCursorError(f"cursor timestamp invalid: {raw!r}") from exc


# ---------------------------------------------------------------------------
# cursor（不透明 base64url JSON；两接口共用编解码）
# ---------------------------------------------------------------------------


def encode_cursor(payload: dict[str, Any]) -> str:
    """``{...}`` → base64url JSON 串（不透明，客户端只回传不解析）。"""
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """base64url JSON 串 → dict；任何非法形都抛 ``HistoryCursorError``。"""
    if not isinstance(cursor, str) or not cursor.strip():
        raise HistoryCursorError("cursor empty")
    raw = cursor.strip()
    try:
        padded = raw + "=" * (-len(raw) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - 统一映射 422
        raise HistoryCursorError("cursor malformed") from exc
    if not isinstance(payload, dict):
        raise HistoryCursorError("cursor payload must be object")
    return payload


def threads_cursor_after(cursor: str) -> tuple[datetime, str]:
    """threads 列表 cursor → keyset ``(last_activity_at, thread_id)``。"""
    payload = decode_cursor(cursor)
    ts_raw = payload.get("la")
    tid = payload.get("tid")
    if not isinstance(ts_raw, str) or not isinstance(tid, str) or not tid:
        raise HistoryCursorError("cursor keys invalid")
    return _parse_dt(ts_raw), tid


def make_threads_cursor(last_activity_at: Any, thread_id: str) -> str:
    """threads 列表下一页游标（末条 keyset 键）。"""
    return encode_cursor({"la": _dt_iso(last_activity_at), "tid": thread_id})


def runs_cursor_after(cursor: str) -> tuple[datetime, str]:
    """history run 分页 cursor → keyset ``(run 首帧 created_at, run_id)``。"""
    payload = decode_cursor(cursor)
    ts_raw = payload.get("ts")
    rid = payload.get("rid")
    if not isinstance(ts_raw, str) or not isinstance(rid, str) or not rid:
        raise HistoryCursorError("cursor keys invalid")
    return _parse_dt(ts_raw), rid


def make_runs_cursor(started_at: Any, run_id: str) -> str:
    """history 下一页游标（末条 run 的首帧时间 + run_id）。"""
    return encode_cursor({"ts": _dt_iso(started_at), "rid": run_id})


# ---------------------------------------------------------------------------
# run 分组 / 状态 / 标题
# ---------------------------------------------------------------------------


def _run_sort_key(run: dict[str, Any]) -> tuple[Any, str]:
    return (run["_first_created_at"], run["run_id"])


def group_events_by_run(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """事件行 → run 分组列表，按 **run 首帧 created_at 升序**（并列 run_id 升序）。

    每组：``{run_id, events(seq 升序), _first_created_at, _last_created_at}``。
    事件缺口（persist 失败历史）如实保留——不伪造、不补帧。
    """
    by_run: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        rid = str(ev.get("run_id") or "")
        if not rid:
            continue
        by_run.setdefault(rid, []).append(ev)
    runs: list[dict[str, Any]] = []
    for rid, rows in by_run.items():
        ordered = sorted(rows, key=lambda e: int(e.get("seq") or 0))
        times = [e.get("created_at") for e in rows if e.get("created_at") is not None]
        runs.append(
            {
                "run_id": rid,
                "events": ordered,
                "_first_created_at": min(times) if times else None,
                "_last_created_at": max(times) if times else None,
            }
        )
    runs.sort(key=_run_sort_key)
    return runs


def run_query(run: dict[str, Any]) -> str:
    """run 的用户问句：``run.start`` payload 可选 ``query`` 键（裁定 A1）。

    存量旧 run 无该键 → 空串（FP-4 由标题降级兜住，不阻塞）。
    """
    for ev in run["events"]:
        if ev.get("event_type") == _EVENT_RUN_START:
            query = (ev.get("payload") or {}).get("query")
            return query if isinstance(query, str) else ""
    return ""


def run_terminal_status(run: dict[str, Any]) -> str:
    """run 终态：``done.status``（缺省 completed）/ error / running。"""
    status = "running"
    for ev in run["events"]:
        et = ev.get("event_type")
        if et == _EVENT_DONE:
            raw = (ev.get("payload") or {}).get("status")
            status = str(raw) if raw else "completed"
        elif et == _EVENT_ERROR:
            status = "error"
    return status


def aggregate_answer(
    run: dict[str, Any],
    *,
    max_chars: int = ANSWER_MAX_CHARS,
) -> tuple[str, bool]:
    """run 的 answer 聚合 → ``(answer, answer_truncated)``。

    终帧 ``{"content", "final": true}`` **优先**（取末条终帧）；无终帧回退
    delta 按 seq 拼接（events 已 seq 升序）。超 ``max_chars`` 截断并标
    ``answer_truncated=True``（N3）。
    """
    finals: list[str] = []
    deltas: list[str] = []
    for ev in run["events"]:
        if ev.get("event_type") != _EVENT_ANSWER:
            continue
        payload = ev.get("payload") or {}
        content = payload.get("content")
        if payload.get("final") is True and isinstance(content, str):
            finals.append(content)
            continue
        delta = payload.get("delta")
        if isinstance(delta, str):
            deltas.append(delta)
    answer = finals[-1] if finals else "".join(deltas)
    if len(answer) > max_chars:
        return answer[:max_chars], True
    return answer, False


def summarize_subtasks(run: dict[str, Any]) -> list[dict[str, Any]]:
    """``subtask.progress`` 帧摘要列表（seq 升序）：seq/role/status + 透传摘要键。"""
    out: list[dict[str, Any]] = []
    for ev in run["events"]:
        if ev.get("event_type") != _EVENT_SUBTASK_PROGRESS:
            continue
        payload = ev.get("payload") or {}
        item: dict[str, Any] = {
            "seq": int(ev.get("seq") or 0),
            "agent_role": str(ev.get("agent_role") or ""),
            "status": str(payload.get("status") or ""),
        }
        # 摘要键透传（帧内已是 _summarize_payload 截断过的安全大小）
        for key in ("subtask_result", "answer_preview", "message", "step"):
            if key in payload:
                item[key] = payload[key]
        out.append(item)
    return out


def collect_hitl_requests(run: dict[str, Any]) -> list[dict[str, Any]]:
    """``hitl.waiting`` 帧的审批请求列表（payload.requests 原样透传）。"""
    out: list[dict[str, Any]] = []
    for ev in run["events"]:
        if ev.get("event_type") != _EVENT_HITL_WAITING:
            continue
        payload = ev.get("payload") or {}
        requests = payload.get("requests")
        if isinstance(requests, list):
            for req in requests:
                if isinstance(req, dict):
                    out.append(req)
    return out


def build_run_view(
    run: dict[str, Any],
    *,
    answer_max_chars: int = ANSWER_MAX_CHARS,
) -> dict[str, Any]:
    """单 run → 消息视图（H2 每 run 一节）。"""
    answer, truncated = aggregate_answer(run, max_chars=answer_max_chars)
    return {
        "run_id": run["run_id"],
        "started_at": _dt_iso(run["_first_created_at"]),
        "query": run_query(run),
        "answer": answer,
        "answer_truncated": truncated,
        "subtasks": summarize_subtasks(run),
        "terminal_status": run_terminal_status(run),
        "hitl": collect_hitl_requests(run),
    }


def paginate_run_views(
    events: list[dict[str, Any]],
    *,
    limit: int,
    cursor: str | None = None,
    answer_max_chars: int = ANSWER_MAX_CHARS,
) -> tuple[list[dict[str, Any]], str | None]:
    """H2：事件行 → run 消息视图一页（run 首帧时间升序 keyset）。

    返回 ``(views, next_cursor)``；``next_cursor`` 为 ``None`` 表示翻尽。
    """
    runs = group_events_by_run(events)
    if cursor is not None:
        after_ts, after_rid = runs_cursor_after(cursor)
        runs = [
            r
            for r in runs
            if (r["_first_created_at"], r["run_id"]) > (after_ts, after_rid)
        ]
    page = runs[:limit]
    views = [build_run_view(r, answer_max_chars=answer_max_chars) for r in page]
    next_cursor = None
    if len(runs) > limit and page:
        last = page[-1]
        next_cursor = make_runs_cursor(last["_first_created_at"], last["run_id"])
    return views, next_cursor


# ---------------------------------------------------------------------------
# threads 列表摘要（H1）
# ---------------------------------------------------------------------------


def thread_title(events: list[dict[str, Any]]) -> str:
    """thread 标题：最早 run 的 ``run.start.query``（裁定 A1 真源）。

    FP-4 降级：无 query（存量旧 run）→ ``run_id 前缀 + 时间``，不阻塞列表。
    """
    runs = group_events_by_run(events)
    if not runs:
        return ""
    first = runs[0]
    query = run_query(first).strip()
    if query:
        title = " ".join(query.split())
        if len(title) > TITLE_MAX_CHARS:
            return title[: TITLE_MAX_CHARS - 1] + "…"
        return title
    started = _dt_iso(first["_first_created_at"])
    return f"{first['run_id'][:8]} {started}".strip()


def latest_run_status(events: list[dict[str, Any]]) -> str:
    """thread 最新 run 的终态（末活动 run = ``_last_created_at`` 最大者）。"""
    runs = group_events_by_run(events)
    if not runs:
        return "running"
    latest = max(
        runs,
        key=lambda r: (r["_last_created_at"], r["run_id"]),
    )
    return run_terminal_status(latest)


def build_thread_summary(
    thread_id: str,
    events: list[dict[str, Any]],
    *,
    last_activity_at: Any,
    run_count: int,
) -> dict[str, Any]:
    """H1 列表单条：字段族 thread_id/title/last_activity_at/run_count/latest_run_status。"""
    return {
        "thread_id": thread_id,
        "title": thread_title(events),
        "last_activity_at": _dt_iso(last_activity_at),
        "run_count": run_count,
        "latest_run_status": latest_run_status(events),
    }
