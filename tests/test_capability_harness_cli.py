"""Host C1 · harness CLI 白名单 Capability 测试（mock subprocess）。

CI/本地不真跑 npx、不装 npm、不断网：asyncio.create_subprocess_exec 全部 mock，
stdout/stderr 用 fixture 字节/JSON。覆盖：解析透传 · policy_blocked 零调用 ·
双键门 · env 缺失不可用 · 参数逃逸拒绝 · 超时 · 非零退出 · 截断 · 禁 shell 模式。
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ops.capability import (
    CapabilitySpec,
    ainvoke,
    get_registry,
    harness_cli,
    invoke,
    list_capabilities,
    register,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.harness_cli import (
    DSH_KIT_VERSION_ENV,
    HARNESS_TASK_LINT_ID,
    HARNESS_VERIFY_ID,
    MAX_STREAM_BYTES,
    TIMEOUT_SECONDS,
    HarnessCliAdapter,
    HarnessCliError,
    register_harness_cli_capabilities,
)

_TASK_PATH = "docs/tasks/active/task_host_harness_cli_capability.md"
_HOST_OPEN = {"_host_policy": {"allow_high_risk": True, "allow_cli": True}}

_VERIFY_FIXTURE = {
    "status": "PASS",
    "task": _TASK_PATH,
    "gates": {"HG-TASK-DRAFT": "approved", "HG-AUDIT-R1": "approved"},
    "checks": {"task_lint": "PASS"},
}


class _FakeProc:
    """create_subprocess_exec 假进程：communicate 回罐头字节；hang 模拟超时。"""

    def __init__(self, stdout=b"", stderr=b"", returncode=0, hang=False):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self._hang = hang
        self.killed = False

    async def communicate(self):
        if self._hang:
            await asyncio.sleep(3600)
        return self._stdout, self._stderr

    def kill(self):
        self.killed = True

    async def wait(self):
        return self.returncode


def _fake_exec(calls: list[dict], proc: _FakeProc):
    async def _impl(*argv, **kwargs):
        calls.append({"argv": argv, "kwargs": kwargs})
        return proc

    return _impl


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """注册表 + env 隔离：Policy/钉版键全部清掉，用例按需显式开。"""
    for key in (
        "OPS_CAPABILITY_ALLOW_HIGH_RISK",
        "OPS_CAPABILITY_ALLOW_CLI",
        DSH_KIT_VERSION_ENV,
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    get_registry().clear()
    ensure_default_capabilities()


# --- 注册机制 ---


def test_not_in_default_registry():
    """00 定夺：不进业务默认目录/探针路径（旧测零破坏锚点）。"""
    ids = {s.capability_id for s in list_capabilities()}
    assert HARNESS_VERIFY_ID not in ids
    assert HARNESS_TASK_LINT_ID not in ids


def test_register_visible_enabled_and_kind_literal_cli():
    newly = register_harness_cli_capabilities()
    assert set(newly) == {HARNESS_VERIFY_ID, HARNESS_TASK_LINT_ID}
    specs = {s.capability_id: s for s in list_capabilities()}
    for cid in (HARNESS_VERIFY_ID, HARNESS_TASK_LINT_ID):
        spec = specs[cid]
        assert spec.enabled is True
        # R1 非阻塞 ③：kind 字面量钉死 cli，否则 allow_cli 门静默漏接
        assert spec.kind == "cli"
        assert spec.risk_level == "high"
    assert HarnessCliAdapter.kind == "cli"
    # 幂等：重复注册不 ValueError（registry 钉死拒绝覆盖），返回空
    assert register_harness_cli_capabilities() == []


# --- Policy 门（先于 adapter · 双键） ---


async def test_policy_blocked_by_default_adapter_zero_calls():
    register_harness_cli_capabilities()
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, _FakeProc())):
        result = await ainvoke(HARNESS_VERIFY_ID, {"task_path": _TASK_PATH})
    assert result.ok is False
    assert "policy_blocked: high_risk" in (result.error or "")
    assert result.meta.get("policy_blocked") is True
    assert calls == []  # Policy 门先于 adapter：零调用


async def test_policy_double_key_required():
    """kind=cli + risk=high：须 allow_high_risk 且 allow_cli 双键同开。"""
    register_harness_cli_capabilities()
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, _FakeProc())):
        only_high = await ainvoke(
            HARNESS_VERIFY_ID,
            {"task_path": _TASK_PATH},
            ctx={"_host_policy": {"allow_high_risk": True}},
        )
        only_cli = await ainvoke(
            HARNESS_VERIFY_ID,
            {"task_path": _TASK_PATH},
            ctx={"_host_policy": {"allow_cli": True}},
        )
    assert "policy_blocked: cli_disabled" in (only_high.error or "")
    assert "policy_blocked: high_risk" in (only_cli.error or "")
    assert calls == []


# --- 成功路径（解析透传 · 命令向量钉死） ---


async def test_verify_success_json_passthrough_via_ctx(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    proc = _FakeProc(stdout=json.dumps(_VERIFY_FIXTURE).encode())
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = await ainvoke(HARNESS_VERIFY_ID, {"task_path": _TASK_PATH}, ctx=_HOST_OPEN)
    assert result.ok is True
    assert result.output == _VERIFY_FIXTURE
    assert result.output["status"] == "PASS"
    assert result.output["gates"]["HG-AUDIT-R1"] == "approved"
    assert len(calls) == 1
    assert calls[0]["argv"] == (
        "npx",
        "--yes",
        "spec-wave@2.4.2",
        "verify",
        "--target",
        ".",
        "--task",
        _TASK_PATH,
        "--json",
    )
    assert calls[0]["kwargs"].get("stdout") == asyncio.subprocess.PIPE
    assert calls[0]["kwargs"].get("stderr") == asyncio.subprocess.PIPE
    assert "shell" not in calls[0]["kwargs"]


async def test_task_lint_success_via_env_open(monkeypatch):
    """Host 策略 env 通道：OPS_CAPABILITY_ALLOW_HIGH_RISK + _CLI 双键放行。"""
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_HIGH_RISK", "true")
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_CLI", "1")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    proc = _FakeProc(stdout=b"PASS task lint", stderr=b"")
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = await ainvoke(
            HARNESS_TASK_LINT_ID, {"op": "task_lint", "task_path": _TASK_PATH}
        )
    assert result.ok is True
    assert result.output["op"] == "task_lint"
    assert result.output["passed"] is True
    assert result.output["exit_code"] == 0
    assert result.output["stdout"] == "PASS task lint"
    assert calls[0]["argv"] == (
        "npx",
        "--yes",
        "spec-wave@2.4.2",
        "task",
        "lint",
        "--file",
        _TASK_PATH,
    )


async def test_lint_wiki_delta_success(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    proc = _FakeProc(stdout=b"PASS lint-wiki-delta", stderr=b"")
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = await ainvoke(
            HARNESS_TASK_LINT_ID, {"op": "lint_wiki_delta"}, ctx=_HOST_OPEN
        )
    assert result.ok is True
    assert result.output["op"] == "lint_wiki_delta"
    assert result.output["passed"] is True
    assert calls[0]["argv"] == (
        "npx",
        "--yes",
        "spec-wave@2.4.2",
        "task",
        "lint-wiki-delta",
        "--target",
        ".",
    )


# --- env 钉版 ---


async def test_env_missing_capability_unavailable():
    register_harness_cli_capabilities()
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, _FakeProc())):
        result = await ainvoke(HARNESS_VERIFY_ID, {"task_path": _TASK_PATH}, ctx=_HOST_OPEN)
    assert result.ok is False
    assert "capability_unavailable" in (result.error or "")
    assert DSH_KIT_VERSION_ENV in (result.error or "")
    assert calls == []  # 不可用：不起子进程（不静默漂版）


async def test_env_pin_invalid_capability_unavailable(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2; rm -rf /")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, _FakeProc())):
        result = await ainvoke(HARNESS_VERIFY_ID, {"task_path": _TASK_PATH}, ctx=_HOST_OPEN)
    assert result.ok is False
    assert "capability_unavailable" in (result.error or "")
    assert calls == []


# --- 参数白名单 ---


@pytest.mark.parametrize(
    "bad_path",
    [
        "../secret.md",
        "docs/tasks/../../etc/passwd",
        "/etc/passwd",
        "~/x.md",
        "C:/tmp/x.md",
        "docs/tasks/active/a.md;rm -rf",
        "docs/tasks/active/a.md && whoami",
        "docs/tasks/active/$(id).md",
        "docs/tasks/active/a|b.md",
        "docs/tasks/active/a b.md",
        "docs\\tasks\\active\\a.md",
        "README.md",
        "docs/tasks",
    ],
)
async def test_task_path_escape_rejected(bad_path, monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, _FakeProc())):
        result = await ainvoke(HARNESS_VERIFY_ID, {"task_path": bad_path}, ctx=_HOST_OPEN)
    assert result.ok is False
    assert "invalid_args" in (result.error or "")
    assert calls == []  # 校验拒绝：不执行


async def test_task_lint_unknown_op_rejected(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, _FakeProc())):
        result = await ainvoke(HARNESS_TASK_LINT_ID, {"op": "status"}, ctx=_HOST_OPEN)
    assert result.ok is False
    assert "invalid_args" in (result.error or "")
    assert calls == []


async def test_non_dict_args_rejected(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, _FakeProc())):
        result = await ainvoke(HARNESS_VERIFY_ID, "docs/tasks/active/x.md", ctx=_HOST_OPEN)
    assert result.ok is False
    # 阶段 H：有 args_schema 时 Gateway 先拒非 object（args_schema_invalid）；
    # adapter 层 invalid_args 仍保留给无 schema / 更深校验路径。
    err = result.error or ""
    assert "args_schema_invalid" in err or "invalid_args" in err
    assert calls == []


# --- 超时 / 非零退出 / JSON 解析失败 / 截断 ---


async def test_timeout_cli_failed_adapter_direct(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    adapter = HarnessCliAdapter(HARNESS_VERIFY_ID, timeout_seconds=0.05)
    proc = _FakeProc(hang=True)
    calls: list[dict] = []
    with (
        patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)),
        pytest.raises(HarnessCliError, match="cli_failed: timeout"),
    ):
        await adapter.ainvoke({"task_path": _TASK_PATH})
    assert proc.killed is True


async def test_timeout_via_gateway_ok_false_not_hang(monkeypatch):
    """超时经 gateway：ok=False 返回不挂起（自定义 id 避免污染稳定 id）。"""
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register(
        CapabilitySpec(
            capability_id="test_harness_timeout",
            kind="cli",
            description="超时探针",
            risk_level="high",
        ),
        HarnessCliAdapter(HARNESS_VERIFY_ID, timeout_seconds=0.05),
    )
    proc = _FakeProc(hang=True)
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = await ainvoke(
            "test_harness_timeout", {"task_path": _TASK_PATH}, ctx=_HOST_OPEN
        )
    assert result.ok is False
    assert "cli_failed: timeout" in (result.error or "")
    assert proc.killed is True


async def test_nonzero_exit_cli_failed_with_stderr(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    proc = _FakeProc(stdout=b"", stderr=b"ERR: W1 gate pending", returncode=1)
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = await ainvoke(
            HARNESS_TASK_LINT_ID,
            {"op": "task_lint", "task_path": _TASK_PATH},
            ctx=_HOST_OPEN,
        )
    assert result.ok is False
    assert "cli_failed" in (result.error or "")
    assert "exit_code=1" in (result.error or "")
    assert "ERR: W1 gate pending" in (result.error or "")


async def test_verify_invalid_json_cli_failed(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    proc = _FakeProc(stdout=b"not-json-output", returncode=0)
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = await ainvoke(HARNESS_VERIFY_ID, {"task_path": _TASK_PATH}, ctx=_HOST_OPEN)
    assert result.ok is False
    assert "cli_failed" in (result.error or "")
    assert "invalid_json" in (result.error or "")


async def test_stdout_truncation(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    big = b"x" * (MAX_STREAM_BYTES + 2048)
    proc = _FakeProc(stdout=big)
    calls: list[dict] = []
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = await ainvoke(
            HARNESS_TASK_LINT_ID, {"op": "lint_wiki_delta"}, ctx=_HOST_OPEN
        )
    assert result.ok is True
    assert "truncated 2048B" in result.output["stdout"]
    assert len(result.output["stdout"]) <= MAX_STREAM_BYTES + len("...[truncated 2048B]")


def test_timeout_and_truncation_constants():
    """R1 非阻塞 ②：30 定数值落断言 —— 120s（≤180s 上限内）· 64 KiB。"""
    assert TIMEOUT_SECONDS == 120.0
    assert TIMEOUT_SECONDS <= 180.0
    assert MAX_STREAM_BYTES == 64 * 1024


# --- 禁令 A：无 shell 模式（grep 断言） ---


def test_no_shell_mode_in_source():
    src = Path(harness_cli.__file__).read_text(encoding="utf-8")
    assert "shell=True" not in src
    assert "create_subprocess_shell" not in src


# --- 同步入口（无运行中事件循环场景） ---


def test_sync_invoke_ok_outside_event_loop(monkeypatch):
    monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.4.2")
    register_harness_cli_capabilities()
    calls: list[dict] = []
    proc = _FakeProc(stdout=b"PASS lint-wiki-delta")
    with patch("asyncio.create_subprocess_exec", new=_fake_exec(calls, proc)):
        result = invoke(HARNESS_TASK_LINT_ID, {"op": "lint_wiki_delta"}, ctx=_HOST_OPEN)
    assert result.ok is True
    assert result.output["passed"] is True
