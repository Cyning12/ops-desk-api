"""P3-T2b · ops.schedule.create 执行体（对话化创建定时任务 · 契约 15 §2）。

本模块是 capability loader 白名单第三前缀（manifest.py
_PREFIX_TO_MODULE["local_fn:app.ops.schedule.service:"]）的宿主模块：
manifest manifests/ops.schedule.v1.yaml 的 adapter 冒号串在加载期经
importlib 运行期解析到 create_schedule_from_capability。

设计钉死（15 §2.4）：

- 执行体**直调 T2 schedule store**（与 §1 REST 同一套归属校验 + 双上限
  20/200 + 词表校验，不复制逻辑）；词表/配额/归属失败 →
  ScheduleValidationError 422 文案**透传不改写**（Agent 原文转述）。
- 幂等：request_id（缺省回退宿主注入 "{run_id}:{subtask_id}" ·
  偏差 D3）经 IdempotencyStore 防重（claim → duplicate 直返首执对账载荷 ·
  in_flight → RuntimeError · 失败 release 可安全重试 · 成功 acomplete）。
- 归属谓词 fail-closed：tenant_id / user_id **只取 ctx**（与 Principal
  同源纪律 · 禁取模型产出）；委派 off 模式 ctx 无 user_id → 不落笔。
- DB IO 延迟 import（store/idempotency 在函数内 · 本模块顶层零 DB 依赖）。
- capability 本身不直接发 run；创建后的点火由 T3 worker 产生 fires（§2.4-4）。
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

_CAPABILITY_ID = "ops.schedule.create"
_DEFAULT_TIMEZONE = "Asia/Shanghai"


def _parse_run_at(raw: Any) -> datetime | None:
    """run_at 字符串 → datetime（naive 由 store._ensure_aware 按 UTC 解释）。"""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"run_at 非合法 ISO 8601 时刻: {text!r}") from exc


def _parse_optional_int(raw: Any, *, field: str) -> int | None:
    """可选整数字段解析（bool 拒 · 非数字拒 · 不落笔）。"""
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise ValueError(f"{field} 必须是整数")
    if isinstance(raw, int):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    try:
        return int(text, 10)
    except ValueError as exc:
        raise ValueError(f"{field} 必须是整数: {text!r}") from exc


def _optional_str(raw: Any) -> str | None:
    text = str(raw or "").strip()
    return text or None


async def create_schedule_from_capability(payload: Any, *, ctx: dict | None = None) -> dict:
    """创建定时任务（ops.schedule.create 执行体 · HITL 批准后由既有闸链调用）。

    防重链路承 defaults.ops_write_run_note 先例：claim →（duplicate 直返 /
    in_flight 拒）→ store.create_schedule → 成功 acomplete / 失败 release。
    """
    args = payload if isinstance(payload, dict) else {}
    thread_id = str(args.get("thread_id") or "").strip()
    name = str(args.get("name") or "").strip()
    instruction = str(args.get("instruction") or "").strip()
    schedule_kind = str(args.get("schedule_kind") or "").strip()
    if not thread_id or not name or not instruction or not schedule_kind:
        raise ValueError(
            "thread_id / name / instruction / schedule_kind 必填（落笔参数缺失不落笔）"
        )

    # 归属谓词只取 ctx（与 Principal 同源 · 禁取模型产出）· 缺谓词 fail-closed
    tenant_id = str((ctx or {}).get("tenant_id") or "").strip()
    if not tenant_id:
        raise PermissionError(
            "tenant_scope_missing：写落笔必须携带租户谓词（ctx.tenant_id · 与 Principal 同源）"
        )
    user_id_raw = str((ctx or {}).get("user_id") or "").strip()
    if not user_id_raw:
        raise PermissionError(
            "user_scope_missing：创建定时任务必须携带调用者谓词"
            "（ctx.user_id · 归属=调用者 · 委派链路注入 · off 模式不落笔）"
        )
    try:
        user_id = uuid.UUID(user_id_raw)
    except ValueError as exc:
        raise ValueError(f"ctx.user_id 非合法 UUID: {user_id_raw!r}") from exc

    # 幂等键：args.request_id 优先；缺省回退宿主注入 "{run_id}:{subtask_id}"
    # （偏差 D3 · HITL resume 重放同 subtask 不双写）；两者皆无 → 不落笔。
    request_id = str(args.get("request_id") or "").strip()
    if not request_id:
        run_id = str((ctx or {}).get("run_id") or "").strip()
        subtask_id = str((ctx or {}).get("subtask_id") or "").strip()
        if run_id and subtask_id:
            request_id = f"{run_id}:{subtask_id}"
    if not request_id:
        raise ValueError("幂等键缺失不落笔（args.request_id 与 ctx.run_id/subtask_id 皆无）")

    run_at = _parse_run_at(args.get("run_at"))
    interval_seconds = _parse_optional_int(args.get("interval_seconds"), field="interval_seconds")
    max_fires = _parse_optional_int(args.get("max_fires"), field="max_fires")
    time_of_day = _optional_str(args.get("time_of_day"))
    tz_name = _optional_str(args.get("timezone")) or _DEFAULT_TIMEZONE

    # 延迟 import：能力面顶层零 DB 依赖（承 defaults/idempotency/receipts 先例）
    from app.ops.capability.idempotency import get_idempotency_store
    from app.ops.schedule import store as schedule_store

    idem = get_idempotency_store()
    aclaim = getattr(idem, "aclaim", None)
    if callable(aclaim):
        claim = await aclaim(request_id, capability_id=_CAPABILITY_ID, tenant_id=tenant_id)
    else:
        claim = await asyncio.to_thread(
            idem.claim, request_id, capability_id=_CAPABILITY_ID, tenant_id=tenant_id
        )
    if claim.duplicate:
        # 命中幂等键：不执行。回一个与首次形状一致的对账载荷（§2.4-2 同键重放）。
        return {
            "tool": _CAPABILITY_ID,
            "written": False,
            "duplicated": True,
            "duplicate_of": claim.receipt_id,
            "idempotency_key": request_id,
            "tenant_id": tenant_id,
        }
    if not claim.acquired:
        raise RuntimeError(
            f"idempotency_in_flight: 同一幂等键正在执行中 key={request_id} tenant={tenant_id}"
        )

    async def _arelease() -> None:
        arelease = getattr(idem, "arelease", None)
        if callable(arelease):
            await arelease(request_id, tenant_id=tenant_id)
        else:
            await asyncio.to_thread(idem.release, request_id, tenant_id=tenant_id)

    approval_id = str((ctx or {}).get("approval_id") or "")
    try:
        # 直调 T2 store（与 REST 同校验路径）：词表外 kind / interval<300 /
        # run_at 非未来 / 双上限 / 非 thread_owner → ScheduleValidationError
        # 422 文案透传不改写（§2.4-3 · 零写）。
        created = await schedule_store.create_schedule(
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
            name=name,
            instruction=instruction,
            schedule_kind=schedule_kind,
            run_at=run_at,
            interval_seconds=interval_seconds,
            time_of_day=time_of_day,
            tz_name=tz_name,
            max_fires=max_fires,
        )
    except Exception:
        # 校验/配额/落笔失败 = 无副作用 → 释放租约，可安全重试
        await _arelease()
        raise

    # 落笔成功：键标完成（回执 id 由 gateway 落完回执后补上 · complete 支持二次调用）
    acomplete = getattr(idem, "acomplete", None)
    if callable(acomplete):
        await acomplete(request_id, tenant_id=tenant_id)
    else:
        await asyncio.to_thread(idem.complete, request_id, tenant_id=tenant_id)

    schedule_id = str(created.get("schedule_id") or "")
    return {
        "tool": _CAPABILITY_ID,
        "written": True,
        "duplicated": False,
        "schedule_id": schedule_id,
        "next_fire_at": created.get("next_fire_at"),
        "status": created.get("status"),
        "humanized_display": created.get("humanized_display"),
        "tenant_id": tenant_id,
        "approval_id": approval_id,
        "idempotency_key": request_id,
        "receipt": {
            "schedule_id": schedule_id,
            "tenant_id": tenant_id,
            "thread_id": thread_id,
            "name": str(created.get("name") or name),
            "schedule_kind": schedule_kind,
        },
    }
