"""HITL 对外端点。

| 端点 | 谁调 | 鉴权 |
|---|---|---|
| ``GET /api/ops/hitl/requests`` | OA / 审批端拉待办 | HMAC 签名 |
| ``GET /api/ops/hitl/requests/{id}`` | 运维 / 前端 | 管理员 |
| ``POST /api/ops/hitl/callback`` | OA 回调审批结果 | HMAC 签名 |
| ``POST /api/ops/hitl/requests/{id}/resume`` | 运维 / 前端 | 管理员 |
| ``GET /api/ops/hitl/pending`` | 浏览器审批列表 | cookie maintainer |
| ``POST /api/ops/hitl/requests/{id}/decide`` | 浏览器批准 / 驳回 | cookie maintainer |

**浏览器决策面（B2）为什么与 OA 签名面并列存在**：签名面是给外部系统
（OA）的机读通道，浏览器拿不到 HMAC 密钥就永远看不到待审批列表。
cookie 面只做两件事——列出**归属当前用户**的 pending、把申请置为已决；
密钥不出服务器，置已决与 callback 同语义（复用 ``store.adecide``），
恢复只有**一条路径**（``resume`` 端点 / T2 自动触发同源复用）——
decide 默认**不自动 resume**（两步钉死），T2 起可按 env/单据配置为 auto。

**恢复这一半为什么单独有驱动器（``hitl/resume.py``）**：
``observe_node`` 用 ``interrupt()`` 把图挂起后，前端停在"等待授权"那一帧、
进程里那次 run 已经不再推进。"批准"只是把库里一行改成 approved ——
要让它真的继续跑，得拿 ``thread_id`` 找到那个 checkpoint 并喂
``Command(resume=...)``。缺了这一步，"批了"和"没批"在界面上长得一样。

**为什么"接收审批结果"要单独做成一个接口，而不是轮询**：
审批是**外部系统**的行为，它发生时本进程可能已经不在同一轮执行里了。
回调让"批准"这件事成为一个**有凭据的事件**（落库 + 签名），
而不是"某次轮询恰好看到了状态变了"。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

from fastapi import APIRouter, Body, Header, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.db.models import OpsUser
from app.ops.deps import AdminSyncAuth, MaintainerUser
from app.ops.hitl import auto_resume, get_hitl_store, new_request_id
from app.ops.hitl.persistence import describe_hitl_persistence
from app.ops.hitl.resume import ResumeError, resume_hitl_run
from app.ops.hitl.signature import (
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    SignatureError,
    secret_configured,
    verify,
)
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl", tags=["hitl"])


def _require_signed(request: Request, body: bytes) -> None:
    """外部系统调用的两个端点共用：签名不通过直接 401。"""
    try:
        verify(body=body, headers=request.headers)
    except SignatureError as exc:
        logger.warning("hitl 回调鉴权失败：%s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.get("/runtime")
async def runtime(_user: OpsUser | None = AdminSyncAuth) -> dict[str, Any]:
    """**审批申请到底落不落库**——不落库时一切照常运行、只是人永远等不到。"""
    info = describe_hitl_persistence()
    info["callback_secret_configured"] = secret_configured()
    return info


@router.get("/requests")
async def list_requests(
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    x_ops_signature: str | None = Header(default=None, alias=HEADER_SIGNATURE),
    x_ops_timestamp: str | None = Header(default=None, alias=HEADER_TIMESTAMP),
    x_ops_nonce: str | None = Header(default=None, alias=HEADER_NONCE),
) -> dict[str, Any]:
    """拉审批申请（OA / 审批端）。``status=pending`` 即"待我批的"。"""
    _require_signed(request, b"")
    rows = await get_hitl_store().alist(status=status_filter, limit=limit)
    return {"items": rows, "count": len(rows)}


@router.get("/requests/{request_id}")
async def get_request(
    request_id: str, _user: OpsUser | None = AdminSyncAuth
) -> dict[str, Any]:
    row = await get_hitl_store().aget(request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    return row


# ---------------------------------------------------------------------------
# 浏览器决策面（cookie maintainer · 裁定 D1/E1 · 与 OA 签名面零交集）
# ---------------------------------------------------------------------------


class _DecidePayload(BaseModel):
    """decide 请求体。``decision`` 只收两种值，非法值由 Pydantic 直接挡成 422。

    ``resume_mode``（T2 · SPEC D5/Q7）：批准后是否自动恢复的可选覆盖键
    （`inherit` 缺省=用全局 env `OPS_HITL_AUTO_RESUME` · `immediate`=立即自动 ·
    `manual`=稍后手动）。**两字段错误形态刻意不同**：decision 非法=Pydantic 层
    **422**（既有形态一行不动）；resume_mode 未知值=端点内手工白名单 **400**
    （R2-N1 · SPEC FP-10/A10 钉死——故本键钉 `str`，禁 Literal/Enum 变 422）。
    """

    decision: Literal["approved", "rejected"]
    note: str = ""
    resume_mode: str = "inherit"


async def _run_owner_of(row: dict[str, Any]) -> str | None:
    """申请 → run 归属用户（裁定 E1 真源：``lg_rag.event_store.run_owner``）。

    HITL 申请行里**没有 user_id**，归属只能经 ``run_id`` 反查事件表。
    解析不到（没 run_id / run 没落过事件帧 / 反查本身失败）→ 返回 ``None``
    并打 **error 日志**；调用方按「排除 / 404」处理，**绝不猜一个 user_id**
    （猜错就是把别人的审批面开给当前用户），也不许因此 500。
    """
    from app.ops.lg_rag.event_store import run_owner

    run_id = str(row.get("run_id") or "").strip()
    if not run_id:
        logger.error("HITL 归属反查：申请 %s 没有 run_id，归属不可判定", row.get("id"))
        return None
    try:
        owner = await run_owner(run_id)
    except Exception:
        logger.exception("HITL 归属反查失败 run=%s request=%s", run_id, row.get("id"))
        return None
    if not owner:
        logger.error(
            "HITL 归属反查：run %s 查不到归属用户（没落过事件帧？）request=%s",
            run_id,
            row.get("id"),
        )
        return None
    return str(owner)


_PENDING_FIELDS = ("id", "run_id", "thread_id", "reason", "blocked_by", "created_at")


@router.get("/pending")
async def list_pending(user: OpsUser = MaintainerUser) -> dict[str, Any]:
    """**浏览器审批列表**：当前 maintainer 可见的 pending 申请（cookie 鉴权）。

    与 OA 签名面 ``GET /requests`` 的差别：这条走 cookie + maintainer 角色，
    且**只返回归属当前用户**的申请（裁定 E1）。归属解析不到的申请
    **排除 + error 日志**——不 500、不泄露；store 本身故障同样降级空列表。
    """
    store = get_hitl_store()
    try:
        rows = await store.alist(status=STATUS_PENDING, limit=200)
    except Exception:
        logger.exception("HITL pending 列表：store.alist 失败，按空列表降级（不 500）")
        return {"items": [], "count": 0}
    me = str(user.id)
    items: list[dict[str, Any]] = []
    for row in rows:
        owner = await _run_owner_of(row)
        if owner is None or owner != me:
            continue
        items.append({key: row.get(key) for key in _PENDING_FIELDS})
    return {"items": items, "count": len(items)}


@router.post("/requests/{request_id}/decide")
async def decide_request(
    request_id: str, payload: _DecidePayload, user: OpsUser = MaintainerUser
) -> dict[str, Any]:
    """**浏览器置已决**：把一条 pending 申请置为 approved / rejected。

    与 OA ``callback`` 同语义（复用 ``store.adecide`` 的 pending 守卫），
    但鉴权是 cookie maintainer——**密钥不出服务器**。

    **两步钉死（SPEC Q2）· T2 起可配置**：默认（manual）本端点只置已决，
    **不自动 resume**——图还挂在 checkpoint 里；客户端第二步调既有
    ``POST /requests/{id}/resume`` 才真正把 run 跑完，响应里的 ``resume`` 块
    把第二步说出来。T2 增（SPEC D5/Q7）：全局 env ``OPS_HITL_AUTO_RESUME=auto``
    或载荷 ``resume_mode=immediate`` 时，decide(approved) 持久化成功后派发
    进程内 asyncio 后台任务走**同一条恢复路径**（``resume`` 块注明已触发）；
    manual 形态响应字面零 diff。

    边界（与 failure_paths 对齐）：
    - 未知 id / 归属他人 / 归属不可判定 → **404**（不泄露存在性，FP-1 口径）；
    - 重复 decide / 已决 → **409**（与 callback 同一判据：``adecide`` 返回 None）；
    - 审计日志只记动作锚点（id/decision/by/at），**不记内容**（SPEC 纪律 #4）。
    """
    # R2-N1：resume_mode 白名单手工校验 → 未知值 400（非 Pydantic 422 · SPEC FP-10/A10）
    if payload.resume_mode not in auto_resume.RESUME_MODES:
        raise HTTPException(
            status_code=400,
            detail="resume_mode 必须是 inherit / immediate / manual",
        )
    store = get_hitl_store()
    row = await store.aget(request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    owner = await _run_owner_of(row)
    if owner is None or owner != str(user.id):
        # 归属不可判定视同非本人：宁可拒掉本人，也不把别人的申请开出来
        raise HTTPException(status_code=404, detail="申请不存在")
    decided = await store.adecide(
        request_id,
        decision=payload.decision,
        by=str(user.username or user.id),
        note=payload.note,
    )
    if decided is None:
        # adecide 只受理 pending，而上面 aget 已证明 id 存在 ⇒ 必已决 —— 与 callback 同语义
        existing = await store.aget(request_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="申请不存在")
        raise HTTPException(
            status_code=409,
            detail=f"申请已是 {existing.get('status')}，不接受重复决定",
        )
    logger.info(
        "HITL 浏览器决策 request=%s decision=%s by=%s at=%s",
        request_id,
        payload.decision,
        user.username,
        time.time(),
    )
    # T2（R2-N2 挂点 · decide 成功分支）：approved ∧ 有效模式=auto → 派发进程内
    # asyncio 后台任务走同源恢复路径。派发不阻响应（失败只落台账 · 实操-F）；
    # OA callback 本波不挂（签名面零 diff · 非范围）——OA 批准单在全局 auto 下
    # 由补偿扫描补触发（N-1 语义明示：不即时 ≠ 不补 · 扫描不看来源）。
    auto_triggered = False
    if (
        payload.decision == STATUS_APPROVED
        and auto_resume.resolve_resume_mode(payload.resume_mode) == auto_resume.MODE_AUTO
    ):
        auto_resume.schedule_auto_resume(
            decided, resume_mode=payload.resume_mode, source="decide"
        )
        auto_triggered = True
    resume_block = {
        # manual 形态字面零 diff：恢复是客户端的第二个显式动作（复用既有 resume 端点）
        "required": True,
        "method": "POST",
        "endpoint": f"/api/ops/hitl/requests/{request_id}/resume",
    }
    if auto_triggered:
        # auto 形态注明已触发自动恢复（客户端无需再点 resume · 仍可兜底手动调）
        resume_block = {
            "required": False,
            "auto_triggered": True,
            "method": "POST",
            "endpoint": f"/api/ops/hitl/requests/{request_id}/resume",
        }
    return {
        "ok": True,
        "request": decided,
        "resume": resume_block,
    }


@router.post("/callback")
async def callback(
    request: Request,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    """接收 OA 的审批结果。

    请求体里带**关联标识**（``request_id`` / ``thread_id`` / ``run_id`` /
    ``checkpoint_id``），它们指明"这次批准的是哪一次 run"；
    **鉴权靠签名头**，不靠这些标识——标识是明文可读的，密钥不是。
    """
    raw = await request.body()
    _require_signed(request, raw)

    request_id = str(payload.get("request_id") or "").strip()
    decision = str(payload.get("decision") or "").strip().lower()
    if not request_id:
        raise HTTPException(status_code=400, detail="缺少 request_id")
    if decision not in (STATUS_APPROVED, STATUS_REJECTED):
        raise HTTPException(
            status_code=400,
            detail=f"decision 必须是 {STATUS_APPROVED} / {STATUS_REJECTED}",
        )

    row = await get_hitl_store().adecide(
        request_id,
        decision=decision,
        by=str(payload.get("decision_by") or payload.get("approver") or "oa"),
        note=str(payload.get("note") or ""),
    )
    if row is None:
        # 要么是 id 不存在，要么已经决过了 —— 后者必须**区分开**，
        # 否则"重复回调"会被当成"申请丢了"
        existing = await get_hitl_store().aget(request_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="申请不存在")
        raise HTTPException(
            status_code=409,
            detail=f"申请已是 {existing.get('status')}，不接受重复决定",
        )
    return {"ok": True, "request": row}


def _same_run(row: dict[str, Any], other: dict[str, Any]) -> bool:
    """两条申请是否属于同一次挂起（run_id 优先，缺失时退回 thread_id）。"""
    run_id = str(row.get("run_id") or "").strip()
    if run_id:
        return str(other.get("run_id") or "").strip() == run_id
    tid = str(row.get("thread_id") or "").strip()
    return bool(tid) and str(other.get("thread_id") or "").strip() == tid


async def _collect_decisions(row: dict[str, Any]) -> tuple[list[str], list[str]]:
    """汇总**同一次挂起**里所有已决申请 → ``(approved, rejected)``。

    为什么不是"只带这一条"：人可能在审批列表里一次批了三条，
    恢复却只带一条 ⇒ 图重跑一次、又被剩下两条拦住、再挂起 ——
    人要连点三次，每次都以为"这次应该完了"。
    批准带的是 ``unlock_subtask_id``（**要解锁重跑**的那一步），
    驳回带 ``subtask_id``（**被否掉**的那一步，仅作记录，不解锁任何东西）。
    """
    approved: list[str] = []
    rejected: list[str] = []
    store = get_hitl_store()
    try:
        rows = await store.alist(limit=200)
    except Exception as exc:  # 拉不全就退回只看这一条，不因此拒绝恢复
        logger.warning("HITL 恢复前汇总同批申请失败，退回单条 err=%r", exc)
        rows = [row]
    for other in rows:
        if not _same_run(row, other):
            continue
        status = str(other.get("status") or "")
        if status == STATUS_APPROVED:
            sid = str(other.get("unlock_subtask_id") or "").strip()
        elif status == STATUS_REJECTED:
            sid = str(other.get("subtask_id") or "").strip()
        else:
            continue
        if sid and sid not in approved and sid not in rejected:
            (approved if status == STATUS_APPROVED else rejected).append(sid)
    return approved, rejected


async def _open_event_sink(row: dict[str, Any], thread_id: str):
    """恢复段的事件落盘器；归属解析不到就返回 ``None``（**并打 error 日志**）。

    为什么不能省：HITL 申请行里没有 user_id，而 replay 按 user_id 校验。
    归属取不到 ⇒ 事件写不进（或写了别人也读不到）⇒ 前端永远停在
    "等待授权"那一帧，而后端日志一片安静。宁可返回 None 也要**报出来**。
    """
    from app.ops.hitl.resume import ResumeEventSink
    from app.ops.lg_rag.event_store import last_seq, run_owner

    run_id = str(row.get("run_id") or "").strip()
    if not run_id:
        logger.error(
            "HITL 恢复：申请 %s 没有 run_id，恢复段事件无处可落 —— 前端 replay 不到",
            row.get("id"),
        )
        return None
    try:
        user_id = await run_owner(run_id)
    except Exception:
        logger.exception("HITL 恢复：run 归属反查失败 run=%s", run_id)
        return None
    if not user_id:
        logger.error(
            "HITL 恢复：run %s 查不到归属用户（没落过事件帧？）—— "
            "恢复段事件不落盘，前端 replay 不到批准后的结论",
            run_id,
        )
        return None
    try:
        start_seq = await last_seq(run_id)
    except Exception:
        logger.exception("HITL 恢复：run %s 取最大 seq 失败，从 0 续写", run_id)
        start_seq = 0
    return ResumeEventSink(
        run_id=run_id, user_id=user_id, thread_id=thread_id, start_seq=start_seq
    )


async def _persist_resumed_turns(sink, outcome: dict[str, Any]) -> None:
    """补落这一轮的 user / assistant turn。

    SSE 在"等待授权"那帧就收尾了，**用户这一轮压根没进历史**。
    恢复完成后必须补上，否则下一轮对话看不到自己问过什么，
    而且批准得来的答案也永远不在 thread 里。
    """
    from app.ops.lg_rag.thread_store import persist_thread_turns

    query = str(outcome.get("query") or "")
    answer = str(outcome.get("answer") or "")
    if not (query or answer):
        return
    try:
        await persist_thread_turns(sink.thread_id, sink.user_id, query, answer)
    except Exception:
        logger.exception("HITL 恢复：补落 thread turns 失败 thread=%s", sink.thread_id)


async def _execute_decided_resume(row: dict[str, Any]) -> dict[str, Any]:
    """**恢复执行体：手动 resume 端点与自动触发同源**（T2 F3 · 无状态恢复纪律）。

    依赖仅 `row`（store 行）：汇总同批决定 → 开事件 sink → `resume_hitl_run`
    → 关 sink + 补落 turns。一律从事件表/DB 重建，**禁 HTTP 自调**、禁第二条
    恢复实现。抛 `ResumeError` 由调用方各自映射：手动端点 → HTTP 状态码；
    自动触发（`auto_resume` 后台任务）→ 只落日志（不改 decide 已返回结果）。
    返回 `{req_status, thread_id, sink, outcome}` 供手动端点组装响应。
    """
    req_status = str(row.get("status") or "")
    approved, rejected = await _collect_decisions(row)
    if not approved and req_status == STATUS_APPROVED:
        # 批准了却拿不到可解锁的步骤 —— 多半是申请行缺 unlock_subtask_id。
        # 必须响，否则拿着空 approved 去恢复 ⇒ 实际按"驳回"收工。
        raise ResumeError(
            "no_unlock", "已批准但拿不到待解锁的步骤（unlock_subtask_id 为空）"
        )
    thread_id = str(row.get("thread_id") or "").strip()
    sink = await _open_event_sink(row, thread_id)
    if sink is not None:
        await sink.open(approved=approved, decided_by=str(row.get("decision_by") or ""))
    outcome = await resume_hitl_run(
        thread_id=thread_id,
        approved=approved,
        rejected=rejected,
        decided_by=str(row.get("decision_by") or ""),
        update_sink=sink,
    )
    # ResumeError 时 sink 不关（与抽取前一致：异常路径不落 done 帧）
    if sink is not None:
        await sink.close()
        await _persist_resumed_turns(sink, outcome)
    logger.info(
        "HITL 恢复完成 request=%s thread=%s approved=%s rejected=%s replay=%s",
        row.get("id"),
        thread_id,
        approved,
        rejected,
        sink.cursor if sink else "",
    )
    return {
        "req_status": req_status,
        "thread_id": thread_id,
        "sink": sink,
        "outcome": outcome,
    }


@router.post("/requests/{request_id}/resume")
async def resume_request(
    request_id: str, _user: OpsUser | None = AdminSyncAuth
) -> dict[str, Any]:
    """审批出结果后**真的把挂起的图恢复起来**。

    两处必须说清，否则"恢复"是个假动作：

    - 批准 ⇒ 解锁（被批准的那一步从不可变前缀里摘出去、旧结果剪掉、
      轮数归零），然后**真的从那个 checkpoint 继续跑**；
    - 驳回 ⇒ 不解锁，收工出结论（结论里带着"这步没做、因为没批"）。

    **驳回也必须能调这个端点**：图正挂在 ``interrupt()`` 上等人，
    如果"只有批准能恢复"，驳回之后那条 run 会**永远挂在等待授权那一帧**，
    前端看着像卡死，而库里清清楚楚写着 rejected。
    """
    row = await get_hitl_store().aget(request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    # ⚠️ 别叫 ``status``：本模块从 fastapi 导入了同名模块，遮蔽了会炸
    req_status = str(row.get("status") or "")
    if req_status not in (STATUS_APPROVED, STATUS_REJECTED):
        raise HTTPException(
            status_code=409,
            detail=f"申请状态为 {req_status or 'unknown'}，只有已决（approved/rejected）才能恢复",
        )
    # 恢复段与自动触发同源（T2 F3）：执行体抛 ResumeError，这里映射 HTTP
    try:
        result = await _execute_decided_resume(row)
    except ResumeError as exc:
        code = {
            "no_thread_id": status.HTTP_409_CONFLICT,
            "no_decision": status.HTTP_409_CONFLICT,
            "not_interrupted": status.HTTP_409_CONFLICT,
            # 旧版本格式残留：不是"这会儿不能恢复"，是"永远恢复不了"，
            # 但仍然归 409（客户端该做的是提示人重开，而不是重试）
            "stranded_checkpoint": status.HTTP_409_CONFLICT,
            # T2 抽取：空 unlock 409 由执行体抛（detail 逐字不变；原路径不打 warning，保持）
            "no_unlock": status.HTTP_409_CONFLICT,
            "checkpointer_not_configured": status.HTTP_503_SERVICE_UNAVAILABLE,
        }.get(exc.code, status.HTTP_502_BAD_GATEWAY)
        if exc.code != "no_unlock":
            logger.warning("HITL 恢复被拒 request=%s code=%s %s", request_id, exc.code, exc.detail)
        raise HTTPException(status_code=code, detail=exc.detail) from exc
    thread_id = result["thread_id"]
    sink = result["sink"]
    outcome = result["outcome"]
    return {
        "ok": True,
        "request": {
            "id": row.get("id"),
            "status": req_status,
            "run_id": row.get("run_id"),
            "thread_id": thread_id,
        },
        "resume": outcome,
        # 前端拿这个 cursor 调 POST /lg-rag/replay 就能收到"批准之后跑完的那段"
        "replay": {
            "run_id": sink.run_id if sink else str(row.get("run_id") or ""),
            "cursor": sink.cursor if sink else "",
            "events_persisted": sink.persisted if sink else 0,
            "events_failed": sink.failed if sink else 0,
            # 归属没解析到 ⇒ 事件没落 ⇒ 前端 replay 不到；**必须说出来**
            "persisted": sink is not None,
            "re_interrupted": bool(sink.re_interrupted) if sink else False,
        },
        "ts": time.time(),
    }


@router.post("/requests")
async def create_request_manual(
    payload: dict[str, Any] = Body(...),
    _user: OpsUser | None = AdminSyncAuth,
) -> dict[str, Any]:
    """手工登记一条审批申请（运维补录 / 联调用）。

    正常路径是编排层自动落库；这个端点只为"人需要补一条"存在。
    """
    request = {
        "id": str(payload.get("id") or new_request_id()),
        "run_id": str(payload.get("run_id") or ""),
        "thread_id": str(payload.get("thread_id") or ""),
        "checkpoint_id": payload.get("checkpoint_id"),
        "tenant_id": str(payload.get("tenant_id") or ""),
        "subtask_id": str(payload.get("subtask_id") or ""),
        "blocked_by": str(payload.get("blocked_by") or "prefix_touch_required"),
        "unlock_subtask_id": str(payload.get("unlock_subtask_id") or ""),
        "reason": str(payload.get("reason") or ""),
        "detail": str(payload.get("detail") or ""),
        "payload": payload.get("payload") or {},
        "status": STATUS_PENDING,
        "created_at": time.time(),
    }
    created = await get_hitl_store().acreate(request)
    return {"ok": True, "request": created}

