"""进程内指标（最小可用）。

**为什么要有**：trace 回答"这一次调用发生了什么"，但回答不了"**整体健康吗**"。
最该被盯的一个数字是：

> **被 Policy 拦下的写操作有多少次**（`write.blocked`）

它异常升高，说明有人在反复尝试不该做的写；它恒为 0，可能是没人用，也可能是
**写闸根本没装上**（配合 `/runtime` 的持久化模式一起看）。

刻意做成**进程内计数 + JSON 快照**，不引 Prometheus 依赖——
要接监控再在 `/metrics` 外面套 exporter，而不是现在就往内核里塞依赖。
多实例下各进程各一份，这是已知边界（与进程内注册表同源）。
"""

from __future__ import annotations

import threading
from typing import Any

from app.ops.capability.errors import error_code_of
from app.ops.capability.types import WRITE_SIDE_EFFECTS, CapabilityResult

_LOCK = threading.Lock()
_BY_CAPABILITY: dict[str, dict[str, int]] = {}
_BY_OUTCOME: dict[str, int] = {}
_WRITE_TOTAL = 0
_WRITE_BLOCKED = 0
_LATENCY_COUNT = 0
_LATENCY_SUM_MS = 0.0
_LATENCY_MAX_MS = 0.0


def outcome_of(result: CapabilityResult) -> str:
    """把结果归成一个可聚合的口径（与稳定错误码对齐）。"""
    if result.ok:
        return "ok"
    if result.meta.get("policy_blocked"):
        return "policy_blocked"
    return error_code_of(str(result.error or "")) or "error"


def is_write_result(result: CapabilityResult) -> bool:
    return str(result.meta.get("side_effect") or "") in WRITE_SIDE_EFFECTS


def record_outcome(result: CapabilityResult) -> None:
    """在 `invoke` / `ainvoke` 的**唯一出口**调用，覆盖全部路径（含 unknown/disabled）。"""
    global _WRITE_TOTAL, _WRITE_BLOCKED
    global _LATENCY_COUNT, _LATENCY_SUM_MS, _LATENCY_MAX_MS

    outcome = outcome_of(result)
    cid = result.capability_id or "<unknown>"
    with _LOCK:
        bucket = _BY_CAPABILITY.setdefault(cid, {})
        bucket[outcome] = bucket.get(outcome, 0) + 1
        _BY_OUTCOME[outcome] = _BY_OUTCOME.get(outcome, 0) + 1
        if is_write_result(result):
            _WRITE_TOTAL += 1
            if not result.ok:
                _WRITE_BLOCKED += 1
        if result.duration_ms is not None:
            _LATENCY_COUNT += 1
            _LATENCY_SUM_MS += float(result.duration_ms)
            _LATENCY_MAX_MS = max(_LATENCY_MAX_MS, float(result.duration_ms))


def snapshot() -> dict[str, Any]:
    with _LOCK:
        total = sum(_BY_OUTCOME.values())
        latency = {
            "count": _LATENCY_COUNT,
            "avg_ms": round(_LATENCY_SUM_MS / _LATENCY_COUNT, 2) if _LATENCY_COUNT else None,
            "max_ms": round(_LATENCY_MAX_MS, 2) if _LATENCY_COUNT else None,
        }
        return {
            "scope": "process_local",
            "total_calls": total,
            "by_outcome": dict(sorted(_BY_OUTCOME.items())),
            "write": {
                "calls": _WRITE_TOTAL,
                "blocked": _WRITE_BLOCKED,
                "allowed": _WRITE_TOTAL - _WRITE_BLOCKED,
            },
            "by_capability": {cid: dict(sorted(b.items())) for cid, b in sorted(_BY_CAPABILITY.items())},
            "latency_ms": latency,
        }


def reset() -> None:
    """测试用。生产不该调。"""
    global _WRITE_TOTAL, _WRITE_BLOCKED
    global _LATENCY_COUNT, _LATENCY_SUM_MS, _LATENCY_MAX_MS
    with _LOCK:
        _BY_CAPABILITY.clear()
        _BY_OUTCOME.clear()
        _WRITE_TOTAL = 0
        _WRITE_BLOCKED = 0
        _LATENCY_COUNT = 0
        _LATENCY_SUM_MS = 0.0
        _LATENCY_MAX_MS = 0.0
