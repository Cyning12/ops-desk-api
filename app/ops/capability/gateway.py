"""Capability Gateway 表面：register / unregister / list / schemas_for_llm / invoke / ainvoke / provide.

P0：Registry + invoke；P1：``schemas_for_llm``（供 bind_tools / ToolNode **可选**）。
P3：``provide``（``kind=skill`` 注入上下文预留；与 ``invoke`` 可执行步骤区分）。

观测（SPEC §5）：``invoke`` / ``provide`` 向**当前** span 写 metadata
（capability_id / kind / ok / error / args 摘要 / policy / subtask_id /
approval_id 预留），不另开根 span，以便 ``tool_exec_node`` 的
``trace_span("tool_exec")`` 兼容复用。

无 ``args_schema`` 行为（P1 钉死）：``schemas_for_llm`` **跳过**该条目；
invoke **不**做参数 schema 校验。有 schema 时校验失败 → ``ok=False``
（``args_schema_invalid``），不抛垮调用方。

进程内**注册表**（非跨进程注册中心）。业务不变量不进 ``args_schema``。

写能力强制 schema（预留）：本仓尚无写能力实现；上路后须强制校验
（env / ``_host_policy.force_args_schema`` 或 kind=write）。

W2 增补：
- 错误口径带**稳定错误码前缀**（``unknown_id:`` / ``disabled:``，见 ``errors``），
  中文详情保留在冒号之后——模型认码，人读详情。
- ``list_capabilities`` / ``schemas_for_llm`` 支持 ``principal``：在 CapabilityFilter
  之上再做一层**身份可见性**裁剪（见 ``visibility``）。
- 写能力调用无论成败都落**副作用回执**（见 ``receipts``）。
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import inspect
import json
import os
import time
from typing import Any

from app.ops.capability.errors import DISABLED, UNKNOWN_ID, format_error
from app.ops.capability.idempotency import get_idempotency_store
from app.ops.capability.policy import check_invoke, write_allowed
from app.ops.capability.receipts import (
    Receipt,
    arecord_receipt,
    build_receipt,
    record_receipt,
)
from app.ops.capability.registry import CapabilityAdapter, CapabilityRegistry
from app.ops.capability.schema_validate import validate_capability_args
from app.ops.capability.types import (
    WRITE_SIDE_EFFECTS,
    CapabilityFilter,
    CapabilityResult,
    CapabilitySpec,
    Principal,
)
from app.ops.capability.visibility import evaluate_visibility
from app.ops.tracing import update_current_span_metadata

# 「未知工具」文案保留（既有调用方与测试按子串断言）；前面加稳定错误码
_UNKNOWN_TEMPLATE = "未知工具"

_ERROR_TRUNCATE = 200
_ARGS_SUMMARY_MAX = 160
_ENV_FORCE_ARGS_SCHEMA = "OPS_CAPABILITY_FORCE_ARGS_SCHEMA"

_registry = CapabilityRegistry()


def get_registry() -> CapabilityRegistry:
    """进程内单例注册表（测试可 ``clear`` / 重注册）。"""
    return _registry


def register(spec: CapabilitySpec, adapter: CapabilityAdapter) -> None:
    """注册能力；重复 id → ValueError（见 registry 模块钉死注释）。"""
    _registry.register(spec, adapter)


def unregister(capability_id: str) -> bool:
    """注销；不存在返回 False。"""
    return _registry.unregister(capability_id)


def list_capabilities(
    *,
    filter: CapabilityFilter | None = None,
    principal: Principal | None = None,
) -> list[CapabilitySpec]:
    """列出可见能力（SPEC 表面名 ``list``；避 builtins 故命名 ``list_capabilities``）。

    两层裁剪：``filter``（场景：kind / 风险 / 写副作用 / tags）→
    ``principal``（身份：部门 / 角色 / 项目 / 密级）。

    ``principal is None`` → 按**匿名主体**求值（``Principal()``）：未声明
    ``visibility`` 的能力照旧可见，声明了限制的能力对匿名主体不可见（fail-closed）。
    需要审计摘要用 :func:`capability_catalog_snapshot`。
    """
    return capability_catalog_snapshot(filter=filter, principal=principal)[0]


def capability_catalog_snapshot(
    *,
    filter: CapabilityFilter | None = None,
    principal: Principal | None = None,
) -> tuple[list[CapabilitySpec], dict[str, Any]]:
    """可见集 + 求值摘要（谁被裁、为什么、多少条未声明 visibility）。

    给 Builder / 审计用：只看 ``list_capabilities`` 拿不到「为什么他没看到」。
    """
    specs = _registry.list_specs(filter=filter)
    return evaluate_visibility(specs, principal or Principal())


def schemas_for_llm(
    *,
    filter: CapabilityFilter | None = None,
    principal: Principal | None = None,
) -> list[dict[str, Any]]:
    """导出 OpenAI / LangChain tools 风格可序列化 schema（SPEC §3.2 · P1）。

    形状（每条）::

        {"type": "function", "function": {"name", "description", "parameters"}}

    Filter / principal 与 ``list_capabilities`` 相同。

    无 ``args_schema``（钉死）：**跳过**该能力，不生成空/残缺 parameters 条目；
    需要 FC 暴露时须在注册时提供 JSON Schema（``CapabilitySpec.args_schema``）。
    """
    out: list[dict[str, Any]] = []
    for spec in list_capabilities(filter=filter, principal=principal):
        if spec.args_schema is None:
            # 钉死：无 args_schema → 跳过（见模块 docstring）
            continue
        out.append(
            {
                "type": "function",
                "function": {
                    "name": spec.capability_id,
                    "description": spec.description,
                    "parameters": copy.deepcopy(spec.args_schema),
                },
            }
        )
    return out


def invoke(
    capability_id: str,
    args: Any = None,
    *,
    ctx: dict[str, Any] | None = None,
) -> CapabilityResult:
    """统一调用；未知 id / adapter 异常 → ``ok=False``，不抛垮调用方（SPEC §3.4 / §6）。

    ``kind=skill``：对应 **可执行步骤**（P3 stub 会 ``NotImplementedError`` → ``ok=False``）；
    注入上下文请用 ``provide``。
    """
    return _dispatch(capability_id, mode="invoke", args=args, ctx=ctx)


async def ainvoke(
    capability_id: str,
    args: Any = None,
    *,
    ctx: dict[str, Any] | None = None,
) -> CapabilityResult:
    """异步调用（P-13）：adapter 有 ``ainvoke`` 或返回 coroutine 则 await；否则走 sync ``invoke``。

    未知 id / adapter 异常 → ``ok=False``，语义与 ``invoke`` 一致。
    """
    return await _adispatch(capability_id, mode="invoke", args=args, ctx=ctx)


def provide(
    capability_id: str,
    *,
    ctx: dict[str, Any] | None = None,
) -> CapabilityResult:
    """``kind=skill`` 预留：注入上下文（SPEC §4 P3）。

    要求 adapter 实现 ``provide(*, ctx)``；无该方法 / 非 skill → ``ok=False``。
    与 ``invoke``（可执行步骤）语义分离；**不**跑完整 Skill 引擎。
    """
    return _dispatch(capability_id, mode="provide", args=None, ctx=ctx)


def _force_args_schema(ctx: dict[str, Any] | None) -> bool:
    if os.environ.get(_ENV_FORCE_ARGS_SCHEMA, "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return True
    if not ctx:
        return False
    host = ctx.get("_host_policy")
    return isinstance(host, dict) and host.get("force_args_schema") is True


def _prepare_call(
    capability_id: str,
    *,
    args: Any,
    ctx: dict[str, Any] | None,
    mode: str,
) -> tuple[CapabilitySpec, Any, float] | CapabilityResult:
    """lookup + enabled + Policy + args_schema；失败返回 CapabilityResult。"""
    cid = capability_id or ""
    started = time.perf_counter()
    entry = _registry.get(cid)
    if entry is None:
        result = CapabilityResult(
            ok=False,
            error=format_error(UNKNOWN_ID, f"{_UNKNOWN_TEMPLATE}: {cid or '(未指定)'}"),
            capability_id=cid,
            duration_ms=0.0,
        )
        _write_span_metadata(result, kind="", risk_level=None, args=args, ctx=ctx)
        return result

    spec, adapter = entry
    if not spec.enabled:
        result = CapabilityResult(
            ok=False,
            error=format_error(DISABLED, f"{_UNKNOWN_TEMPLATE}: {cid}"),
            capability_id=cid,
            duration_ms=0.0,
            meta={"blocked": "disabled"},
        )
        _write_span_metadata(
            result,
            kind=spec.kind,
            risk_level=spec.risk_level,
            args=args,
            ctx=ctx,
        )
        return result

    policy = check_invoke(spec, ctx=ctx)
    if not policy.allowed:
        result = CapabilityResult(
            ok=False,
            error=policy.reason or "policy_blocked",
            capability_id=cid,
            duration_ms=0.0,
            meta={"policy_blocked": True, "kind": spec.kind},
        )
        _write_span_metadata(
            result,
            kind=spec.kind,
            risk_level=spec.risk_level,
            policy_blocked=True,
            policy_reason=policy.reason,
            args=args,
            ctx=ctx,
        )
        return result

    # provide 无 args；invoke 有 schema 才校验（force 预留：无 schema 时亦拒绝写路径）
    if mode == "invoke":
        schema_err = validate_capability_args(args, spec.args_schema)
        if schema_err is None and spec.args_schema is None and _force_args_schema(ctx):
            # 强制模式预留：无 schema 的能力在 force 下拒（写能力上路后启用）
            schema_err = "args_schema_invalid: force_args_schema 要求已声明 schema"
        if schema_err is not None:
            result = CapabilityResult(
                ok=False,
                error=schema_err,
                capability_id=cid,
                duration_ms=0.0,
                meta={"kind": spec.kind, "args_schema_invalid": True},
            )
            _write_span_metadata(
                result,
                kind=spec.kind,
                risk_level=spec.risk_level,
                policy_reason="args_schema_ok",
                args=args,
                ctx=ctx,
            )
            return result

    return spec, adapter, started


def _build_receipt(
    spec: CapabilitySpec,
    result: CapabilityResult,
    *,
    ctx: dict[str, Any] | None,
) -> tuple[Receipt | None, str | None]:
    """构建回执并回填 meta；返回 ``(receipt | None, idempotency_key | None)``。

    ``receipt is None`` 有两种情况：不该留（只读且无 capture），或**命中幂等键没真执行**。
    """
    is_write = spec.side_effect in WRITE_SIDE_EFFECTS
    if not is_write and not spec.receipt_capture:
        return None, None
    captured: dict[str, Any] = {}
    key: str | None = None
    duplicated = False
    if isinstance(result.output, dict):
        raw_captured = result.output.get("receipt")
        if isinstance(raw_captured, dict):
            captured = raw_captured
        raw_key = result.output.get("idempotency_key")
        key = str(raw_key) if raw_key else None
        duplicated = result.output.get("duplicated") is True

    if duplicated:
        # 命中幂等键：本次**没有执行**，按「没执行就没有副作用」不留回执，
        # 也不重复 complete（否则会把原回执 id 覆盖掉，duplicate_of 就对不上了）
        result.meta["duplicated"] = True
        result.meta["side_effect"] = spec.side_effect
        return None, key

    receipt = build_receipt(
        capability_id=spec.capability_id,
        side_effect=spec.side_effect,
        ok=result.ok,
        ctx=ctx,
        idempotency_key=key,
        captured=captured,
        error=result.error,
        write_confirmed=write_allowed(ctx),
    )
    result.meta["receipt_id"] = receipt.receipt_id
    result.meta["side_effect"] = spec.side_effect
    return receipt, key


def _tenant_of(ctx: dict[str, Any] | None) -> str:
    c = ctx or {}
    return str(c.get("tenant_id") or c.get("_host_tenant") or "")


def _maybe_record_receipt(
    spec: CapabilitySpec,
    result: CapabilityResult,
    *,
    ctx: dict[str, Any] | None,
) -> None:
    """同步路径：写能力无论成败都落回执（见 ``receipts`` 模块 docstring）。"""
    receipt, key = _build_receipt(spec, result, ctx=ctx)
    if receipt is None:
        return
    record_receipt(receipt)
    # 幂等键在这一刻才算「完成」——因为回执 id 此刻才有，才能把「键 ↔ 回执」对上。
    # 只在成功时 complete：失败的状态由 adapter 决定（无副作用则 release，
    # 否则保持 in_flight 交给租约）——**不要把失败当成完成**。
    if key and result.ok:
        # tenant_id 必须传：防重键的作用域是**租户内**，不传会落到空租户上，
        # 于是 complete 找不到那一行、状态永远停在 in_flight（静默失效）。
        get_idempotency_store().complete(
            key, receipt_id=receipt.receipt_id, tenant_id=_tenant_of(ctx)
        )


async def _amaybe_record_receipt(
    spec: CapabilitySpec,
    result: CapabilityResult,
    *,
    ctx: dict[str, Any] | None,
) -> None:
    """异步路径：DB 版 sink / store 只有异步接口，不能在这里同步调用（会阻塞事件循环）。"""
    receipt, key = _build_receipt(spec, result, ctx=ctx)
    if receipt is None:
        return
    await arecord_receipt(receipt)
    if not (key and result.ok):
        return
    tenant = _tenant_of(ctx)
    store = get_idempotency_store()
    acomplete = getattr(store, "acomplete", None)
    if callable(acomplete):
        await acomplete(key, receipt_id=receipt.receipt_id, tenant_id=tenant)
    else:
        await asyncio.to_thread(
            store.complete, key, receipt_id=receipt.receipt_id, tenant_id=tenant
        )


def _ok_result(
    *,
    spec: CapabilitySpec,
    cid: str,
    mode: str,
    output: Any,
    started: float,
    args: Any,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    duration_ms = (time.perf_counter() - started) * 1000.0
    result = CapabilityResult(
        ok=True,
        output=output,
        capability_id=cid,
        duration_ms=duration_ms,
        meta={"kind": spec.kind, "mode": mode},
    )
    _maybe_record_receipt(spec, result, ctx=ctx)
    _write_span_metadata(
        result,
        kind=spec.kind,
        risk_level=spec.risk_level,
        policy_reason="allowed",
        args=args,
        ctx=ctx,
        side_effect=spec.side_effect,
        receipt_id=result.meta.get("receipt_id"),
    )
    return result


def _err_result(
    *,
    spec: CapabilitySpec,
    cid: str,
    mode: str,
    started: float,
    exc: BaseException,
    args: Any,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    duration_ms = (time.perf_counter() - started) * 1000.0
    result = CapabilityResult(
        ok=False,
        error=repr(exc),
        capability_id=cid,
        duration_ms=duration_ms,
        meta={"kind": spec.kind, "mode": mode},
    )
    # 失败也要留：一次「失败」的写操作可能已经在下游生效（超时 / 半成功）
    _maybe_record_receipt(spec, result, ctx=ctx)
    _write_span_metadata(
        result,
        kind=spec.kind,
        risk_level=spec.risk_level,
        policy_reason="allowed",
        args=args,
        ctx=ctx,
        side_effect=spec.side_effect,
        receipt_id=result.meta.get("receipt_id"),
    )
    return result


async def _aok_result(
    *,
    spec: CapabilitySpec,
    cid: str,
    mode: str,
    output: Any,
    started: float,
    args: Any,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    """异步路径的成功结果（回执走异步 sink，不阻塞事件循环）。"""
    result = CapabilityResult(
        ok=True,
        output=output,
        capability_id=cid,
        duration_ms=(time.perf_counter() - started) * 1000.0,
        meta={"kind": spec.kind, "mode": mode},
    )
    await _amaybe_record_receipt(spec, result, ctx=ctx)
    _write_span_metadata(
        result,
        kind=spec.kind,
        risk_level=spec.risk_level,
        policy_reason="allowed",
        args=args,
        ctx=ctx,
        side_effect=spec.side_effect,
        receipt_id=result.meta.get("receipt_id"),
    )
    return result


async def _aerr_result(
    *,
    spec: CapabilitySpec,
    cid: str,
    mode: str,
    started: float,
    exc: BaseException,
    args: Any,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    """异步路径的失败结果。**失败也要留回执**：一次"失败"的写可能已在下游生效。"""
    result = CapabilityResult(
        ok=False,
        error=repr(exc),
        capability_id=cid,
        duration_ms=(time.perf_counter() - started) * 1000.0,
        meta={"kind": spec.kind, "mode": mode},
    )
    await _amaybe_record_receipt(spec, result, ctx=ctx)
    _write_span_metadata(
        result,
        kind=spec.kind,
        risk_level=spec.risk_level,
        policy_reason="allowed",
        args=args,
        ctx=ctx,
        side_effect=spec.side_effect,
        receipt_id=result.meta.get("receipt_id"),
    )
    return result


def _missing_provide_result(
    *,
    spec: CapabilitySpec,
    cid: str,
    started: float,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    result = CapabilityResult(
        ok=False,
        error=f"adapter 无 provide(): {cid} (kind={spec.kind})",
        capability_id=cid,
        duration_ms=(time.perf_counter() - started) * 1000.0,
        meta={"kind": spec.kind, "mode": "provide"},
    )
    _write_span_metadata(
        result,
        kind=spec.kind,
        risk_level=spec.risk_level,
        args=None,
        ctx=ctx,
    )
    return result


def _dispatch(
    capability_id: str,
    *,
    mode: str,
    args: Any,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    """内部：lookup + enabled 检查 + invoke/provide 分派。"""
    prepared = _prepare_call(capability_id, args=args, ctx=ctx, mode=mode)
    if isinstance(prepared, CapabilityResult):
        return prepared
    spec, adapter, started = prepared
    cid = capability_id or ""
    try:
        if mode == "provide":
            provide_fn = getattr(adapter, "provide", None)
            if not callable(provide_fn):
                return _missing_provide_result(
                    spec=spec, cid=cid, started=started, ctx=ctx
                )
            output = provide_fn(ctx=ctx)
        else:
            output = adapter.invoke(args, ctx=ctx)
        return _ok_result(
            spec=spec,
            cid=cid,
            mode=mode,
            output=output,
            started=started,
            args=args,
            ctx=ctx,
        )
    except Exception as exc:
        return _err_result(
            spec=spec,
            cid=cid,
            mode=mode,
            started=started,
            exc=exc,
            args=args,
            ctx=ctx,
        )


async def _call_adapter_async(
    adapter: Any,
    *,
    mode: str,
    args: Any,
    ctx: dict[str, Any] | None,
) -> Any:
    """adapter.ainvoke 或 coroutine fn 则 await；否则走 sync invoke。"""
    if mode == "provide":
        provide_fn = getattr(adapter, "provide", None)
        if not callable(provide_fn):
            raise TypeError("adapter 无 provide()")
        output = provide_fn(ctx=ctx)
        if inspect.isawaitable(output):
            return await output
        return output

    ainvoke_fn = getattr(adapter, "ainvoke", None)
    if callable(ainvoke_fn):
        output = ainvoke_fn(args, ctx=ctx)
        if inspect.isawaitable(output):
            return await output
        return output
    output = adapter.invoke(args, ctx=ctx)
    if inspect.isawaitable(output):
        return await output
    return output


async def _adispatch(
    capability_id: str,
    *,
    mode: str,
    args: Any,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    """异步分派：coroutine adapter 则 await，否则兼容 sync invoke。"""
    prepared = _prepare_call(capability_id, args=args, ctx=ctx, mode=mode)
    if isinstance(prepared, CapabilityResult):
        return prepared
    spec, adapter, started = prepared
    cid = capability_id or ""
    try:
        if mode == "provide":
            provide_fn = getattr(adapter, "provide", None)
            if not callable(provide_fn):
                return _missing_provide_result(
                    spec=spec, cid=cid, started=started, ctx=ctx
                )
        output = await _call_adapter_async(
            adapter, mode=mode, args=args, ctx=ctx
        )
        return await _aok_result(
            spec=spec,
            cid=cid,
            mode=mode,
            output=output,
            started=started,
            args=args,
            ctx=ctx,
        )
    except Exception as exc:
        return await _aerr_result(
            spec=spec,
            cid=cid,
            mode=mode,
            started=started,
            exc=exc,
            args=args,
            ctx=ctx,
        )


def _args_summary(args: Any) -> str:
    """截断/哈希摘要；禁全量密钥形字段。"""
    if args is None:
        return ""
    if isinstance(args, dict):
        redacted: dict[str, Any] = {}
        for key, value in args.items():
            low = str(key).lower()
            if any(
                s in low
                for s in ("secret", "token", "password", "api_key", "credential")
            ):
                redacted[key] = "***"
            else:
                redacted[key] = value
        try:
            text = json.dumps(redacted, ensure_ascii=False, default=str)
        except TypeError:
            text = str(redacted)
    else:
        text = str(args)
    if len(text) <= _ARGS_SUMMARY_MAX:
        return text
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{text[:_ARGS_SUMMARY_MAX]}…#{digest}"


def _write_span_metadata(
    result: CapabilityResult,
    *,
    kind: str,
    risk_level: str | None = None,
    policy_blocked: bool = False,
    policy_reason: str | None = None,
    args: Any = None,
    ctx: dict[str, Any] | None = None,
    side_effect: str | None = None,
    receipt_id: str | None = None,
) -> None:
    """附加到当前 span；无父 span / 未开启 tracing 时静默。"""
    payload: dict[str, Any] = {
        "capability_id": result.capability_id,
        "kind": kind,
        "ok": result.ok,
        "args_summary": _args_summary(args),
        # 写路径 HITL 预留（本波可空）
        "approval_id": (ctx or {}).get("approval_id") if ctx else None,
    }
    if risk_level is not None:
        payload["risk_level"] = risk_level
    # 副作用维度与 risk_level **并列**上报：审计要能按「有没有副作用」筛
    if side_effect is not None:
        payload["side_effect"] = side_effect
    if receipt_id:
        payload["receipt_id"] = receipt_id
    if policy_blocked:
        payload["policy_blocked"] = True
    if policy_reason is not None:
        payload["policy"] = policy_reason
    elif policy_blocked:
        payload["policy"] = result.error or "policy_blocked"
    else:
        payload["policy"] = "allowed" if result.ok else (result.error or "error")
    if ctx:
        sid = ctx.get("subtask_id")
        if sid is not None:
            payload["subtask_id"] = sid
    if result.error:
        payload["error"] = result.error[:_ERROR_TRUNCATE]
    update_current_span_metadata(payload)
