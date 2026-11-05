"""Host V1-A · 委派令牌接线（D2 签发点 / D3 验签门 / D5 scope 矩阵 / 三档模式）。

覆盖（task 验收 D2/D3/D5 映射）：
- 签发接线：subtask_join 分发路径逐 tool 子任务签发，随 Send 载荷注入 state；
- 审批双路径：只读自动签发（token_issued）/ 写能力 HITL（token_issue_hitl_required
  + 复用既有 hitl 回路落 ops_hitl_requests）；
- 全链路携令牌：分发 → tool_exec 携令牌 → capability 验签通过（fake adapter）；
- replan 重签发：同 subtask 重签发 = 新例生效 + 旧 nonce 作废（R-d）；
- 三档模式：off 零 diff / observe would_block 不拦 / enforce 拒；
- requested_scope 声明∩裁剪矩阵（越界剔除 / 未声明兼容 / 只收窄不放宽 / 64 截断）；
- 非委派调用方（ctx 无 _delegation_required）零影响。
"""

from __future__ import annotations

import json
import logging
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import (
    CapabilitySpec,
    LocalFnAdapter,
    ensure_default_capabilities,
    get_registry,
    invoke,
    register,
)
from app.ops.capability import delegation as dl
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _join_subtasks,
    _observe,
    _persist_hitl,
    route_next_subtask,
    supervisor_node,
    tool_exec_node,
)
from app.ops.strategy.builder import MAX_SCOPE_IDS, effective_scope_from_requested

SECRET = "wiring-secret-0001"
READ_CAP = "test_delegation_read_cap"
WRITE_CAP = "test_delegation_write_cap"


@pytest.fixture(autouse=True)
def _clean_state():
    dl.reset_delegation_state()
    yield
    dl.reset_delegation_state()
    get_registry().clear()
    ensure_default_capabilities()


@pytest.fixture
def enforce_env(monkeypatch):
    monkeypatch.setenv(dl.ENV_MODE, "enforce")
    monkeypatch.setenv(dl.ENV_SECRET, SECRET)
    return monkeypatch


def _register_caps():
    calls: list = []
    register(
        CapabilitySpec(
            capability_id=READ_CAP,
            kind="local_fn",
            description="只读探针",
            side_effect="read",
        ),
        LocalFnAdapter(lambda args: calls.append(args) or {"echo": args}),
    )
    register(
        CapabilitySpec(
            capability_id=WRITE_CAP,
            kind="local_fn",
            description="写探针",
            side_effect="write",
        ),
        LocalFnAdapter(lambda args: calls.append(args) or {"echo": args}),
    )
    return calls


def _state(tool: str, **over) -> dict:
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state = {
        "messages": [HumanMessage(content="查一下部署情况")],
        "run_id": run_id,
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": "查部署",
                "tool": tool,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [sid],
        "allowed_capability_ids": [tool],
    }
    state.update(over)
    return state


# ---------------------------------------------------------------------------
# D2 · 签发接线 + 三档模式
# ---------------------------------------------------------------------------


def test_dispatch_issues_token_into_send_payload(enforce_env, caplog):
    _register_caps()
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        sends = route_next_subtask(_state(READ_CAP))
    assert isinstance(sends, list) and len(sends) == 1
    payload = sends[0].arg
    assert sends[0].node == "tool_exec"
    token = dl.token_from_dict(payload["delegation_token"])
    assert token.capability_set == {READ_CAP}
    assert token.subject_binding["run_id"] == payload["run_id"]
    assert token.subject_binding["subtask_id"] == payload["assigned_subtask"]["subtask_id"]
    assert token.subject_binding["tenant_id"] == "ops-desk-pilot"
    assert "token_issued" in caplog.text


def test_off_mode_dispatch_zero_diff(monkeypatch):
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.setenv(dl.ENV_SECRET, SECRET)
    _register_caps()
    state = _state(READ_CAP)
    sends = route_next_subtask(state)
    payload = sends[0].arg
    assert "delegation_token" not in payload
    # run_id 随载荷下发与委派档无关（fix-worker-state-send-run-id · 案 A ·
    # HG-WORKER-STATE-RUN-ID-DESIGN 裁决）：写审批消费门须从工人可见 state 取到
    # run_id，resume 后重下发才不 fail-closed 再拦。off 模式零 diff 契约收窄为
    # 「不注入委派 artifact」，载荷身份键 run_id 不在该契约面内。
    assert payload["run_id"] == state["run_id"]


def test_off_mode_invalid_value_falls_back(monkeypatch):
    monkeypatch.setenv(dl.ENV_MODE, "bogus")
    _register_caps()
    sends = route_next_subtask(_state(READ_CAP))
    assert "delegation_token" not in sends[0].arg


# ---------------------------------------------------------------------------
# D2 · 审批双路径（只读自动 / 写能力 HITL）
# ---------------------------------------------------------------------------


async def test_readonly_subtask_auto_approved(enforce_env):
    _register_caps()
    state = _state(READ_CAP)
    out = await _join_subtasks({**state, "inflight_subtask_ids": []})
    sid = state["subtasks"][0]["subtask_id"]
    assert sid in out["inflight_subtask_ids"]
    assert "subtask_results" not in out


async def test_write_capability_requires_hitl(enforce_env, caplog):
    _register_caps()
    state = _state(WRITE_CAP)
    sid = state["subtasks"][0]["subtask_id"]
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        out = await _join_subtasks({**state, "inflight_subtask_ids": []})
    assert sid not in out.get("inflight_subtask_ids", [])
    blocked = [r for r in out["subtask_results"] if r.get("hitl_required") is True]
    assert len(blocked) == 1
    assert blocked[0]["blocked_by"] == "delegation_issue_hitl_required"
    assert "token_issue_hitl_required" in caplog.text


@pytest.mark.asyncio
async def test_hitl_required_persists_via_existing_hitl_loop(enforce_env):
    """签发审批复用既有 hitl 回路：被拦子任务落 ops_hitl_requests（不建新审批面）。"""
    _register_caps()
    store = InMemoryHitlStore()
    set_hitl_store(store)
    try:
        state = _state(WRITE_CAP)
        sid = state["subtasks"][0]["subtask_id"]
        joined = await _join_subtasks({**state, "inflight_subtask_ids": []})
        merged = {
            **state,
            "subtask_results": list(joined.get("subtask_results") or []),
            "inflight_subtask_ids": joined.get("inflight_subtask_ids") or [],
        }
        obs = _observe(merged)
        assert obs["hitl_pending"] == [sid]
        created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-1")
        assert unpersisted is False
        rows = await store.alist(status="pending", limit=10)
        assert any(
            str(r.get("blocked_by") or "") == "delegation_issue_hitl_required"
            and str(r.get("subtask_id") or "") == sid
            for r in rows
        )
        assert any(str(r.get("subtask_id") or "") == sid for r in created)
    finally:
        reset_hitl_store()


# ---------------------------------------------------------------------------
# D3 · 全链路携令牌 / 六类拒绝接线 / 三档模式
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_chain_tool_exec_verifies(enforce_env, caplog):
    calls = _register_caps()
    sends = route_next_subtask(_state(READ_CAP))
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        out = await tool_exec_node(sends[0].arg)
    result = out["subtask_results"][0]
    assert "error" not in result
    assert result["output"] == {"echo": "查部署"}
    assert calls == ["查部署"]
    assert "token_verified" in caplog.text


@pytest.mark.asyncio
async def test_enforce_rejects_without_token(enforce_env, caplog):
    """声明收窄把 tool 裁掉 → 空集不签发 → enforce 按 R-a 拒（不落回执）。"""
    calls = _register_caps()
    sends = route_next_subtask(_state(READ_CAP, delegation_scope=[]))
    payload = sends[0].arg
    assert "delegation_token" not in payload
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        out = await tool_exec_node(payload)
    result = out["subtask_results"][0]
    assert "permission_denied" in (result.get("error") or "")
    assert calls == []  # 验签门在 lookup 之前拦下，adapter 零调用
    assert "token_rejected:no_token" in caplog.text


@pytest.mark.asyncio
async def test_observe_mode_would_block_not_blocked(monkeypatch, caplog):
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    monkeypatch.setenv(dl.ENV_SECRET, SECRET)
    calls = _register_caps()
    sends = route_next_subtask(_state(READ_CAP, delegation_scope=[]))
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        out = await tool_exec_node(sends[0].arg)
    result = out["subtask_results"][0]
    assert "error" not in result  # observe 不拦
    assert len(calls) == 1
    assert "token_rejected:no_token" in caplog.text
    assert "would_block" in caplog.text


@pytest.mark.asyncio
async def test_enforce_missing_secret_refuses_issue_and_call(monkeypatch, caplog):
    """enforce 缺密钥 → 拒绝签发+告警（安全默认拒 · 不降级为不签名）。"""
    monkeypatch.setenv(dl.ENV_MODE, "enforce")
    monkeypatch.delenv(dl.ENV_SECRET, raising=False)
    calls = _register_caps()
    with caplog.at_level(logging.WARNING, logger="app.ops.capability.delegation"):
        sends = route_next_subtask(_state(READ_CAP))
    assert "拒绝签发" in caplog.text
    assert "delegation_token" not in sends[0].arg
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        out = await tool_exec_node(sends[0].arg)
    result = out["subtask_results"][0]
    assert "permission_denied" in (result.get("error") or "")
    assert calls == []
    # 缺密钥 → 签发被拒 → 无令牌下发 → 验签门按 R-a no_token 拒（secret_missing
    # 类别仅在「有令牌但无密钥可验」时出现，单测面见 test_capability_delegation）
    assert "token_rejected:no_token" in caplog.text


@pytest.mark.asyncio
async def test_replan_reissue_supersedes_old_nonce(enforce_env, caplog):
    """replan/重发 = 重签发新例；旧例 nonce 作废（R-d）+ token_superseded 审计。"""
    _register_caps()
    state = _state(READ_CAP)
    first = route_next_subtask(state)[0].arg
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        second = route_next_subtask(state)[0].arg
    assert first["delegation_token"] != second["delegation_token"]
    assert "token_superseded" in caplog.text
    # 新例生效
    ok_out = await tool_exec_node(second)
    assert "error" not in ok_out["subtask_results"][0]
    # 旧例重放 → R-d 拒
    old_out = await tool_exec_node(first)
    error = old_out["subtask_results"][0].get("error") or ""
    assert "permission_denied" in error
    assert "nonce_reused" in error


def test_non_delegation_caller_unaffected_in_enforce(enforce_env):
    """非委派调用方（ctx 无 _delegation_required）：enforce 下也零影响。"""
    result = invoke("mock_get_deploy_info", "prod")
    assert result.ok is True


# ---------------------------------------------------------------------------
# D5 · requested_scope 声明∩裁剪矩阵
# ---------------------------------------------------------------------------


def test_scope_matrix_intersect_and_strip(caplog):
    allowlist = {"a", "b"}
    # 声明收窄生效 + 越界剔除（只收窄不放宽）
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.builder"):
        scope, stripped, truncated = effective_scope_from_requested(["a", "evil_id"], allowlist)
    assert scope == ["a"]
    assert stripped == ["evil_id"]
    assert truncated == []
    assert "scope_stripped" in caplog.text
    # 未声明 → 兼容现状隐式 allowlist
    scope_none, stripped_none, _ = effective_scope_from_requested(None, allowlist)
    assert set(scope_none) == allowlist
    assert stripped_none == []
    # 非 list → 视同未声明（承 subtasks cap 外宽容纪律）
    scope_bad, _, _ = effective_scope_from_requested("not-a-list", allowlist)
    assert set(scope_bad) == allowlist


def test_scope_matrix_truncation(caplog):
    allowlist = {f"cap-{i}" for i in range(80)}
    declared = [f"cap-{i}" for i in range(MAX_SCOPE_IDS + 6)]
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.builder"):
        scope, stripped, truncated = effective_scope_from_requested(declared, allowlist)
    assert len(scope) == MAX_SCOPE_IDS
    assert len(truncated) == 6
    assert "scope_truncated" in caplog.text


def test_scope_only_narrows_never_widens():
    scope, stripped, _ = effective_scope_from_requested(
        ["in-allowlist", "not-in-allowlist"], {"in-allowlist"}
    )
    assert "not-in-allowlist" not in scope
    assert stripped == ["not-in-allowlist"]


@pytest.mark.asyncio
async def test_supervisor_writes_effective_scope(monkeypatch):
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    monkeypatch.setenv(dl.ENV_SECRET, SECRET)
    plan = {
        "subtasks": [
            {
                "id": "t1",
                "type": "tool",
                "input": "查部署",
                "tool": "mock_get_deploy_info",
            }
        ],
        "requested_scope": ["mock_get_deploy_info", "evil_id"],
    }
    provider = SimpleNamespace(
        complete=AsyncMock(return_value=json.dumps(plan, ensure_ascii=False))
    )
    state = {
        "messages": [HumanMessage(content="查部署")],
        "run_id": f"run-{uuid.uuid4().hex[:8]}",
        "allowed_capability_ids": ["mock_get_deploy_info"],
    }
    with patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider):
        out = await supervisor_node(state)
    assert out["delegation_scope"] == ["mock_get_deploy_info"]


@pytest.mark.asyncio
async def test_supervisor_undeclared_scope_writes_nothing(monkeypatch):
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    monkeypatch.setenv(dl.ENV_SECRET, SECRET)
    plan = {
        "subtasks": [
            {
                "id": "t1",
                "type": "tool",
                "input": "查部署",
                "tool": "mock_get_deploy_info",
            }
        ]
    }
    provider = SimpleNamespace(
        complete=AsyncMock(return_value=json.dumps(plan, ensure_ascii=False))
    )
    state = {
        "messages": [HumanMessage(content="查部署")],
        "run_id": f"run-{uuid.uuid4().hex[:8]}",
        "allowed_capability_ids": ["mock_get_deploy_info"],
    }
    with patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider):
        out = await supervisor_node(state)
    assert "delegation_scope" not in out  # 未声明 = 兼容现状隐式 allowlist
