"""Capability Gateway 表面：register / unregister / list / schemas_for_llm / invoke / provide。

P0：Registry + invoke；P1：``schemas_for_llm``（供 bind_tools / ToolNode **可选**）。
P3：``provide``（``kind=skill`` 注入上下文预留；与 ``invoke`` 可执行步骤区分）。

观测（SPEC §5）：``invoke`` / ``provide`` 向**当前** span 写 metadata（capability_id / kind / ok / error 截断），
不另开根 span，以便 ``tool_exec_node`` 的 ``trace_span("tool_exec")`` 兼容复用。

无 ``args_schema`` 行为（P1 钉死）：``schemas_for_llm`` **跳过**该条目，不输出残缺 FC schema。
"""

from __future__ import annotations

import copy
import time
from typing import Any

from app.ops.capability.registry import CapabilityAdapter, CapabilityRegistry
from app.ops.capability.types import (
    CapabilityFilter,
    CapabilityResult,
    CapabilitySpec,
)
from app.ops.tracing import update_current_span_metadata

_ERROR_TRUNCATE = 200

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


def _dispatch(
    capability_id: str,
    *,
    mode: str,
    args: Any,
    ctx: dict[str, Any] | None,
) -> CapabilityResult:
    """内部：lookup + enabled 检查 + invoke/provide 分派。"""
    cid = capability_id or ""
    entry = _registry.get(cid)
    started = time.perf_counter()
    if entry is None:
        result = CapabilityResult(
            ok=False,
            error=f"未知工具: {cid or '(未指定)'}",
            capability_id=cid,
            duration_ms=0.0,
        )
        _write_span_metadata(result, kind="")
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
        _write_span_metadata(result, kind=spec.kind)
        return result

    try:
        if mode == "provide":
            provide_fn = getattr(adapter, "provide", None)
            if not callable(provide_fn):
                result = CapabilityResult(
                    ok=False,
                    error=f"adapter 无 provide(): {cid} (kind={spec.kind})",
                    capability_id=cid,
                    duration_ms=(time.perf_counter() - started) * 1000.0,
                    meta={"kind": spec.kind, "mode": "provide"},
                )
                _write_span_metadata(result, kind=spec.kind)
                return result
            output = provide_fn(ctx=ctx)
        else:
            output = adapter.invoke(args, ctx=ctx)
        duration_ms = (time.perf_counter() - started) * 1000.0
        result = CapabilityResult(
            ok=True,
            output=output,
            capability_id=cid,
            duration_ms=duration_ms,
            meta={"kind": spec.kind, "mode": mode},
        )
        _write_span_metadata(result, kind=spec.kind)
        return result
    except Exception as exc:
        duration_ms = (time.perf_counter() - started) * 1000.0
        result = CapabilityResult(
            ok=False,
            error=repr(exc),
            capability_id=cid,
            duration_ms=duration_ms,
            meta={"kind": spec.kind, "mode": mode},
        )
        _write_span_metadata(result, kind=spec.kind)
        return result


def _write_span_metadata(result: CapabilityResult, *, kind: str) -> None:
    """附加到当前 span；无父 span / 未开启 tracing 时静默。"""
    payload: dict[str, Any] = {
        "capability_id": result.capability_id,
        "kind": kind,
        "ok": result.ok,
    }
    if result.error:
        payload["error"] = result.error[:_ERROR_TRUNCATE]
    update_current_span_metadata(payload)
