"""默认 local_fn 能力：两枚 mock + utc_now_iso + 本库 issue/PR lookup。

进程内注册表默认条目（非注册中心）。``args_schema`` 仅参数形态；
业务不变量不进 schema。lookup 标 ``tenant_scoped=True``。
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

from app.ops.capability.adapters.local_fn import LocalFnAdapter
from app.ops.capability.gateway import get_registry, register
from app.ops.capability.lookups import get_issue_by_number, get_pr_by_number
from app.ops.capability.types import CapabilitySpec

# 最小 schema：兼容 legacy 字符串 payload + 结构化 object
_SCHEMA_STRING_OR_OBJECT: dict[str, Any] = {
    "type": ["string", "object"],
    "properties": {},
    "additionalProperties": True,
}

_SCHEMA_LOOKUP: dict[str, Any] = {
    "type": ["string", "object"],
    "properties": {
        "number": {
            "type": ["integer", "string"],
            "description": "issue/PR 号",
        },
    },
    "additionalProperties": True,
}

_SCHEMA_UTC: dict[str, Any] = {
    "type": ["string", "object", "null"],
    "properties": {},
    "additionalProperties": True,
}


def mock_get_issue_status(payload: str) -> dict:
    """罐头数据：issue 状态查询（真实 GitHub API 另议）。"""
    return {
        "tool": "mock_get_issue_status",
        "input": payload,
        "issue": "#128",
        "status": "open",
        "assignee": "cyning",
        "updated_at": "2026-08-20",
    }


def mock_get_deploy_info(payload: str) -> dict:
    """罐头数据：部署信息查询（真实部署平台 API 另议）。"""
    return {
        "tool": "mock_get_deploy_info",
        "input": payload,
        "env": "prod",
        "version": "v2.3.1",
        "deployed_at": "2026-08-19",
        "status": "healthy",
    }


def utc_now_iso(_payload: str) -> dict:
    """只读：返回当前 UTC ISO 时间戳（无副作用 · 不连外网）。"""
    from datetime import datetime

    return {
        "tool": "utc_now_iso",
        "utc": datetime.now(UTC).isoformat(),
        "note": "只读时间查询",
    }


def testing_write_echo(payload: Any) -> dict:
    """测试专用罐头：写操作**语义 mock · 无真实写操作**。

     供 `manifests/testing.v1.yaml` 的 `testing.write.echo` 使用
    （仅 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载 · 不进 `_DEFAULT_SPECS`）。
     纯函数返回罐头 dict：**零 IO · 零 DB · 零外网 · 零文件写 · 零 subprocess**
    （函数体不 import 任何 IO 库，对齐 `utc_now_iso` 范式）。
    """
    return {
        "tool": "testing_write_echo",
        "input": payload,
        "written": False,
        "note": "语义 mock · 无真实写操作（testing-write-capability 测试专用）",
    }


_DEFAULT_SPECS: list[tuple[CapabilitySpec, LocalFnAdapter]] = [
    (
        CapabilitySpec(
            capability_id="mock_get_issue_status",
            kind="local_fn",
            description="Mock：查询 issue 状态（罐头数据）",
            args_schema=dict(_SCHEMA_STRING_OR_OBJECT),
            tags=("mock", "issue"),
            risk_level="low",
            side_effect="read",
            output_fields=("tool", "input", "issue", "status", "assignee", "updated_at"),
        ),
        LocalFnAdapter(mock_get_issue_status),
    ),
    (
        CapabilitySpec(
            capability_id="mock_get_deploy_info",
            kind="local_fn",
            description="Mock：查询部署信息（罐头数据）",
            args_schema=dict(_SCHEMA_STRING_OR_OBJECT),
            tags=("mock", "deploy"),
            risk_level="low",
            side_effect="read",
            output_fields=("tool", "input", "env", "version", "deployed_at", "status"),
        ),
        LocalFnAdapter(mock_get_deploy_info),
    ),
    (
        CapabilitySpec(
            capability_id="utc_now_iso",
            kind="local_fn",
            description="只读：返回当前 UTC ISO 时间戳",
            args_schema=dict(_SCHEMA_UTC),
            tags=("readonly", "time"),
            risk_level="low",
            side_effect="read",
            output_fields=("tool", "utc", "note"),
        ),
        LocalFnAdapter(utc_now_iso),
    ),
    (
        CapabilitySpec(
            capability_id="get_issue_by_number",
            kind="local_fn",
            description="本库只读：按 number 查 Issue 摘要（无 raw_payload）",
            args_schema=dict(_SCHEMA_LOOKUP),
            tags=("lookup", "issue", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=True,
            output_fields=("number", "title", "state", "html_url", "updated_at", "labels", "body"),
        ),
        LocalFnAdapter(get_issue_by_number),
    ),
    (
        CapabilitySpec(
            capability_id="get_pr_by_number",
            kind="local_fn",
            description="本库只读：按 number 查 PR 摘要（无 raw_payload）",
            args_schema=dict(_SCHEMA_LOOKUP),
            tags=("lookup", "pr", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=True,
            output_fields=("number", "title", "state", "html_url", "updated_at", "ci_status", "draft", "body"),
        ),
        LocalFnAdapter(get_pr_by_number),
    ),
]


def ensure_default_capabilities() -> None:
    """幂等注册默认 mock；优先 builtin YAML，缺文件回退硬编码。"""
    # 延迟 import：manifest 解析 adapter 时回指本模块
    from app.ops.capability.manifest import (
        BUILTIN_MANIFEST_PATH,
        load_capability_manifest,
    )

    if BUILTIN_MANIFEST_PATH.is_file():
        load_capability_manifest(BUILTIN_MANIFEST_PATH)
        return
    registry = get_registry()
    for spec, adapter in _DEFAULT_SPECS:
        if registry.get(spec.capability_id) is None:
            register(spec, adapter)
