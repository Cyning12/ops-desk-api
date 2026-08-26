"""默认 local_fn 能力：原 ``MOCK_TOOLS`` 两枚 mock（罐头数据，不连外网）。"""

from __future__ import annotations

from app.ops.capability.adapters.local_fn import LocalFnAdapter
from app.ops.capability.gateway import get_registry, register
from app.ops.capability.types import CapabilitySpec


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


_DEFAULT_SPECS: list[tuple[CapabilitySpec, LocalFnAdapter]] = [
    (
        CapabilitySpec(
            capability_id="mock_get_issue_status",
            kind="local_fn",
            description="Mock：查询 issue 状态（罐头数据）",
            tags=("mock", "issue"),
            risk_level="low",
        ),
        LocalFnAdapter(mock_get_issue_status),
    ),
    (
        CapabilitySpec(
            capability_id="mock_get_deploy_info",
            kind="local_fn",
            description="Mock：查询部署信息（罐头数据）",
            tags=("mock", "deploy"),
            risk_level="low",
        ),
        LocalFnAdapter(mock_get_deploy_info),
    ),
]


def ensure_default_capabilities() -> None:
    """幂等注册默认 mock；已存在则跳过（兼容测试 clear 后重调）。"""
    registry = get_registry()
    for spec, adapter in _DEFAULT_SPECS:
        if registry.get(spec.capability_id) is None:
            register(spec, adapter)
