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
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
import time
from typing import Any

from app.ops.capability.policy import check_invoke
from app.ops.capability.registry import CapabilityAdapter, CapabilityRegistry
from app.ops.capability.schema_validate import validate_capability_args
from app.ops.capability.types import (
    CapabilityFilter,
    CapabilityResult,
    CapabilitySpec,
)
from app.ops.tracing import update_current_span_metadata

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
    *, filter: CapabilityFilter | None = None
) -> list[CapabilitySpec]:
    """列出可见能力（SPEC 表面名 ``list``；避 builtins 故命名 ``list_capabilities``）。"""
    return _registry.list_specs(filter=filter)


def schemas_for_llm(
    *, filter: CapabilityFilter | None = None
) -> list[dict[str, Any]]:
    """导出 OpenAI / LangChain tools 风格可序列化 schema（SPEC §3.2 · P1）。

    形状（每条）::

        {"type": "function", "function": {"name", "description", "parameters"}}

    Filter 与 ``list_capabilities`` 相同。

    无 ``args_schema``（钉死）：**跳过**该能力，不生成空/残缺 parameters 条目；
    需要 FC 暴露时须在注册时提供 JSON Schema（``CapabilitySpec.args_schema``）。
    """
    out: list[dict[str, Any]] = []
    for spec in list_capabilities(filter=filter):
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
            error=f"未知工具: {cid or '(未指定)'}",
            capability_id=cid,
            duration_ms=0.0,
        )
        _write_span_metadata(result, kind="", risk_level=None, args=args, ctx=ctx)
        return result

    spec, adapter = entry
    if not spec.enabled:
        result = CapabilityResult(
            ok=False,
            error=f"未知工具: {cid}",
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
    _write_span_metadata(
        result,
        kind=spec.kind,
        risk_level=spec.risk_level,
        policy_reason="allowed",
        args=args,
        ctx=ctx,
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
    _write_span_metadata(
        result,
        kind=spec.kind,
        risk_level=spec.risk_level,
        policy_reason="allowed",
        args=args,
        ctx=ctx,
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
