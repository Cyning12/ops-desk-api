"""Host C1 · harness CLI 白名单 Capability（harness.verify / harness.task_lint）。

SPEC：docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md（signed）§3/§7/§8；
Task：docs/tasks/active/task_host_harness_cli_capability.md（00 定夺钉死）。

钉死项：

- 命令向量硬编码 npx --yes spec-wave@<env pin> ... 三形态；子进程走
  asyncio.create_subprocess_exec 逐 argv 传入，**禁止 shell 模式**（SPEC §3 禁令 A）。
- kit 版本由 env DSH_CODING_KIT_VERSION 钉版；缺失/非法 → capability_unavailable
  （非静默漂版，SPEC §7）。
- 参数白名单：task_path 必须落在 docs/tasks/ 内；拒绝对路径 / .. 逃逸 /
  反斜杠 / shell 元字符（invalid_args: 前缀族，与 policy_blocked: /
  cli_failed: 同族，便于 C4 /obs 投影聚合）。
- 超时 TIMEOUT_SECONDS = 120（≤180s 上限内，30 定）→ cli_failed: timeout；
  stdout/stderr 各截断 MAX_STREAM_BYTES = 64 KiB（30 定）。
- Policy：risk_level="high" + kind="cli"（字面量钉死，policy allow_cli
  门只认 "cli"）；默认关 → gateway policy_blocked；开启须 Host 双键
  allow_high_risk + allow_cli（env OPS_CAPABILITY_ALLOW_* 或
  ctx._host_policy）。本模块**不改**默认。
- 注册走代码路径 gateway.register（manifest builtin.v1.yaml 仅 local_fn，
  不适用 subprocess cli adapter）；**不**挂进 ensure_default_capabilities /
  probes 默认目录（业务默认目录保持仅 local_fn · capability 旧测零破坏），
  Host 侧显式调用 register_harness_cli_capabilities()。

harness.status：**本波不做**（SPEC §7 可选；C4 开工时补）。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
from typing import Any

from app.ops.capability.gateway import get_registry, register
from app.ops.capability.types import CapabilitySpec

# --- 稳定 id / env 键（单测 · 文档引用） ---

DSH_KIT_VERSION_ENV = "DSH_CODING_KIT_VERSION"
HARNESS_VERIFY_ID = "harness.verify"
HARNESS_TASK_LINT_ID = "harness.task_lint"

# 超时/截断数值（30 定 · task 钉 ≤180s 上限；截断上限方向）
TIMEOUT_SECONDS = 120.0
MAX_STREAM_BYTES = 64 * 1024

# task_lint 子操作（00 定夺：task lint / lint-wiki-delta 两形态）
OP_TASK_LINT = "task_lint"
OP_LINT_WIKI_DELTA = "lint_wiki_delta"

_TASK_PATH_PREFIX = "docs/tasks/"
# 白名单字符集：字母/数字/_/./-// —— shell 元字符与空格天然被拒
_TASK_PATH_RE = re.compile(r"^[A-Za-z0-9_./-]+$")
# npm 版本/dist-tag 形态（如 1.10.0 / latest）；防 env 注入进 argv
_KIT_PIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


class HarnessCliError(RuntimeError):
    """受控错误；message 采用 <family>: <detail> 前缀族。

    前缀族：capability_unavailable: / cli_failed: / invalid_args:
    （与 gateway 侧 policy_blocked: 同族）。
    """


def _kit_pin() -> str:
    """读 env 钉版；缺失/非法 → capability_unavailable（不静默漂版）。"""
    pin = os.environ.get(DSH_KIT_VERSION_ENV, "").strip()
    if not pin:
        raise HarnessCliError(
            f"capability_unavailable: env {DSH_KIT_VERSION_ENV} 未设置（钉版缺失）"
        )
    if not _KIT_PIN_RE.match(pin):
        raise HarnessCliError(f"capability_unavailable: env {DSH_KIT_VERSION_ENV} 非法值: {pin!r}")
    return pin


def _validate_task_path(value: Any) -> str:
    """task_path 白名单校验：docs/tasks/ 内 · 拒绝对路径/.. 逃逸/shell 元字符。"""
    if not isinstance(value, str) or not value.strip():
        raise HarnessCliError("invalid_args: task_path 必须为非空字符串")
    path = value.strip()
    if path.startswith(("/", "\\", "~")) or (len(path) > 1 and path[1] == ":"):
        raise HarnessCliError(f"invalid_args: task_path 拒绝对路径: {path!r}")
    if "\\" in path:
        raise HarnessCliError(f"invalid_args: task_path 拒绝反斜杠: {path!r}")
    if ".." in path:
        raise HarnessCliError(f"invalid_args: task_path 拒绝 .. 逃逸: {path!r}")
    if not _TASK_PATH_RE.match(path):
        raise HarnessCliError(f"invalid_args: task_path 含非法字符: {path!r}")
    if not path.startswith(_TASK_PATH_PREFIX):
        raise HarnessCliError(f"invalid_args: task_path 须在 {_TASK_PATH_PREFIX} 内: {path!r}")
    return path


def _build_argv(capability_id: str, args: Any) -> tuple[list[str], str]:
    """硬编码命令向量；返回 (argv, op 标签)。白名单外一律 invalid_args。"""
    if args is not None and not isinstance(args, dict):
        raise HarnessCliError("invalid_args: args 必须为 dict")
    payload: dict[str, Any] = args or {}
    base = ["npx", "--yes", f"spec-wave@{_kit_pin()}"]
    if capability_id == HARNESS_VERIFY_ID:
        task_path = _validate_task_path(payload.get("task_path"))
        return (
            [*base, "verify", "--target", ".", "--task", task_path, "--json"],
            "verify",
        )
    if capability_id == HARNESS_TASK_LINT_ID:
        op = payload.get("op")
        if op == OP_TASK_LINT:
            task_path = _validate_task_path(payload.get("task_path"))
            return ([*base, "task", "lint", "--file", task_path], op)
        if op == OP_LINT_WIKI_DELTA:
            return ([*base, "task", "lint-wiki-delta", "--target", "."], op)
        raise HarnessCliError(
            f"invalid_args: 未知 task_lint 子操作: {op!r}"
            f"（允许: {OP_TASK_LINT} / {OP_LINT_WIKI_DELTA}）"
        )
    raise HarnessCliError(f"invalid_args: 未知 capability_id: {capability_id!r}")


def _truncate(data: bytes, limit: int) -> str:
    """按字节截断后解码（UTF-8 replace），附截断标记。"""
    if len(data) <= limit:
        return data.decode("utf-8", errors="replace")
    head = data[:limit].decode("utf-8", errors="replace")
    return f"{head}...[truncated {len(data) - limit}B]"


class HarnessCliAdapter:
    """harness.* 白名单 CLI adapter。

    kind 字面量钉死 "cli"：policy allow_cli 门只认该字面，
    改其他值会导致双键门静默漏接（R1 非阻塞 ③）。
    """

    kind = "cli"

    def __init__(
        self,
        capability_id: str,
        *,
        timeout_seconds: float = TIMEOUT_SECONDS,
        max_stream_bytes: int = MAX_STREAM_BYTES,
    ) -> None:
        self._capability_id = capability_id
        self._timeout_seconds = timeout_seconds
        self._max_stream_bytes = max_stream_bytes

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        """同步入口：仅允许无运行中事件循环场景（P-13）；Host 侧用 ainvoke。"""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.ainvoke(args, ctx=ctx))
        raise HarnessCliError("cli_failed: 运行中事件循环内禁同步 invoke；请用 ainvoke（P-13）")

    async def ainvoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
        del ctx  # Policy 已由 gateway 前置；adapter 不消费 ctx
        argv, op = _build_argv(self._capability_id, args)
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=self._timeout_seconds
            )
        except TimeoutError:
            proc.kill()
            with contextlib.suppress(Exception):  # kill 后清理尽力而为
                await proc.wait()
            raise HarnessCliError(f"cli_failed: timeout({self._timeout_seconds:g}s)") from None
        stdout = _truncate(stdout_b, self._max_stream_bytes)
        stderr = _truncate(stderr_b, self._max_stream_bytes)
        returncode = proc.returncode if proc.returncode is not None else -1
        if returncode != 0:
            raise HarnessCliError(f"cli_failed: exit_code={returncode} stderr={stderr}")
        if self._capability_id == HARNESS_VERIFY_ID:
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise HarnessCliError(f"cli_failed: invalid_json stdout={stdout[:200]!r}") from exc
            if not isinstance(parsed, dict):
                raise HarnessCliError(
                    f"cli_failed: invalid_json（期望 object）stdout={stdout[:200]!r}"
                )
            return parsed
        return {
            "op": op,
            "passed": True,
            "exit_code": 0,
            "stdout": stdout,
            "stderr": stderr,
        }


_VERIFY_ARGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "task_path": {
            "type": "string",
            "description": "docs/tasks/ 内 task 文件相对路径",
        },
    },
    "required": ["task_path"],
    "additionalProperties": False,
}

_TASK_LINT_ARGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "op": {
            "type": "string",
            "enum": [OP_TASK_LINT, OP_LINT_WIKI_DELTA],
            "description": "task_lint（须带 task_path）/ lint_wiki_delta",
        },
        "task_path": {
            "type": "string",
            "description": "op=task_lint 时必填；docs/tasks/ 内相对路径",
        },
    },
    "required": ["op"],
    "additionalProperties": False,
}

_HARNESS_SPECS: tuple[CapabilitySpec, ...] = (
    CapabilitySpec(
        capability_id=HARNESS_VERIFY_ID,
        kind="cli",
        description="Host harness：spec-wave verify --json（env 钉版 · Policy 默认关）",
        args_schema=_VERIFY_ARGS_SCHEMA,
        tags=("harness", "cli", "host", "whitelist"),
        risk_level="high",
    ),
    CapabilitySpec(
        capability_id=HARNESS_TASK_LINT_ID,
        kind="cli",
        description="Host harness：task lint / lint-wiki-delta 两子操作（env 钉版 · Policy 默认关）",
        args_schema=_TASK_LINT_ARGS_SCHEMA,
        tags=("harness", "cli", "host", "whitelist"),
        risk_level="high",
    ),
)


def register_harness_cli_capabilities() -> list[str]:
    """幂等注册 harness.* 白名单 Capability（代码路径 gateway.register）。

    已注册则跳过（重复 id 永不覆盖，见 registry 钉死）；返回本次新注册 id 列表。
    **不**被 ensure_default_capabilities / probes 默认路径自动调用。
    """
    registry = get_registry()
    newly: list[str] = []
    for spec in _HARNESS_SPECS:
        if registry.get(spec.capability_id) is not None:
            continue
        register(spec, HarnessCliAdapter(spec.capability_id))
        newly.append(spec.capability_id)
    return newly
