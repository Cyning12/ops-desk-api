"""确定性评估器（E2-b）。

对照 ROADMAP §3.2 score 名：acc.route_match / acc.strategy.allowlist_match / acc.plan_match。
本波只返回 1/0，不写 Langfuse。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

# 与 app.ops.lg_rag.nodes.ROUTES 一致
ROUTES = frozenset({"rag", "direct", "refuse"})
# 与 app.ops.lg_rag.multi.nodes.SUBTASK_TYPES 一致
SUBTASK_TYPES = frozenset({"rag", "extract", "tool"})


def require_expect(case: dict[str, Any], *keys: str) -> dict[str, Any]:
    """fixture 必须含 expect 及指定键；缺则 fail（禁止 silent skip）。"""
    case_id = case.get("id", "<unknown>")
    expect = case.get("expect")
    if not isinstance(expect, dict):
        raise AssertionError(f"fixture {case_id} 缺 expect 键")
    missing = [k for k in keys if k not in expect]
    if missing:
        raise AssertionError(f"fixture {case_id} expect 缺 {missing}")
    return expect


def eval_route_match(actual: str, expect: str) -> int:
    """acc.route_match：route 枚举相等 → 1/0。"""
    if expect not in ROUTES:
        raise ValueError(f"expect.route 非法: {expect!r} 不在 {sorted(ROUTES)}")
    return int(actual == expect)


def eval_allowlist_match(actual: Sequence[str], expect: Sequence[str]) -> int:
    """acc.strategy.allowlist_match：集合相等 → 1/0。"""
    return int(set(actual) == set(expect))


def eval_tool_ids_in_allowlist(
    subtasks: Sequence[dict[str, Any]],
    allowlist: Sequence[str],
) -> int:
    """type=tool 的 tool id 须 ∈ allowlist；非法 → 0。"""
    allowed = frozenset(allowlist)
    for item in subtasks:
        if str(item.get("type") or "") != "tool":
            continue
        tool_id = str(item.get("tool") or "").strip()
        if not tool_id or tool_id not in allowed:
            return 0
    return 1


def eval_plan_schema(subtasks: object) -> int:
    """acc.plan_match 分项：规范化 plan JSON schema。

    每项须有非空 id / input；type ∈ {rag, extract, tool}；
    type=tool 时 tool 非空。
    """
    if not isinstance(subtasks, list) or not subtasks:
        return 0
    for item in subtasks:
        if not isinstance(item, dict):
            return 0
        if not str(item.get("id") or "").strip():
            return 0
        if item.get("type") not in SUBTASK_TYPES:
            return 0
        if not str(item.get("input") or "").strip():
            return 0
        if item.get("type") == "tool" and not str(item.get("tool") or "").strip():
            return 0
    return 1


def eval_subtask_types(
    subtasks: Sequence[dict[str, Any]],
    expect_types: Sequence[str],
) -> int:
    """subtask_types 列表相等（含顺序）。"""
    actual = [str(s.get("type") or "") for s in subtasks]
    return int(actual == list(expect_types))
