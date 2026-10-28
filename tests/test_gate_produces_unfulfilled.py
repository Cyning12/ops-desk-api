"""task lg-rag-gate-produces-unfulfilled：判定 3 收窄 + 带内逃生口指引。

实证 run d3a49527929248cc953b7a5327cae2d0（635 事件 · 400s · budget_exhausted）：
t1 成功终态但实际产出与声明 produces 不符（声明 ['title','body','status']，
产出缺 status）；t2 consumes 已收敛 ['title','body'] 全部真实命中，仍被闸
判定 3「produces 未兑现」拦 contract_missing_field——拦因与 consumes 无关，
而前驱已终态锁定、重规划改不动它的声明 → 两轮照抄 → 预算耗尽。

- **B1**：produces 未兑现且缺失字段未被本步 consumes 引用 → 放行 +
  观察留痕（span 既有通道 _record_span_metadata，不新增事件类型）；
  consumes 引用缺失字段仍由判定 2 拦截（语义零回归）；纯序依赖同放行。
- **B2**：失败摘要段在 contract_missing_field / prefix_touch_required 场景
  附「重发前驱步」逃生口指引；无失败步主路径 prompt 逐字节零 diff
  （零 diff 钉死由 test_supervisor_replan_error_feedback TC4 承担）。
"""

from __future__ import annotations

from unittest.mock import patch

from app.ops.lg_rag.multi import nodes
from app.ops.lg_rag.multi import step_contract as sc
from app.ops.lg_rag.multi.nodes import _join_subtasks

_RUN = "rund3a49"
_T1 = f"{_RUN}:1"
_T2 = f"{_RUN}:2"


def _t1_row() -> dict:
    """d3a49 同形 t1：声明 ['title','body','status']。"""
    return {
        "id": _T1,
        "subtask_id": _T1,
        "alias": "t1",
        "type": "tool",
        "tool": "mock_get_issue",
        "input": "查工单",
        "depends_on": [],
        "produces": ["title", "body", "status"],
    }


def _t1_terminal() -> dict:
    """d3a49 同形 t1 成功终态：实际产出缺 status。"""
    return {
        "id": _T1,
        "subtask_id": _T1,
        "type": "tool",
        "output": {"title": "网络故障", "body": "已受理"},
    }


def _t2_row(consumes: dict | None = None) -> dict:
    row = {
        "id": _T2,
        "subtask_id": _T2,
        "alias": "t2",
        "type": "tool",
        "tool": "mock_notify",
        "input": "发通知",
        "depends_on": [_T1],
    }
    if consumes:
        row["consumes_resolved"] = consumes
    return row


# ---------------------------------------------------------------------------
# B1 · 判定 3 收窄：放行 + 观察留痕
# ---------------------------------------------------------------------------


def test_d3a49_unconsumed_unfulfilled_produces_passes_with_observation():
    """验收①：consumes 全部命中、前驱 produces 部分未兑现 → 放行 + 留痕。

    收窄前本场景返回 contract_missing_field——那正是 d3a49 死锁拦因。
    """
    row = _t2_row(consumes={_T1: ["title", "body"]})
    reason, detail = sc.gate(
        row=row,
        terminals={_T1: _t1_terminal()},
        by_id={_T1: _t1_row()},
        prefix_ids=frozenset(),
    )
    assert reason is None, "consumes 全部命中时 produces 未兑现不得再拦"
    assert detail == ""
    observed = sc.unfulfilled_produces(
        row=row,
        terminals={_T1: _t1_terminal()},
        by_id={_T1: _t1_row()},
    )
    assert observed == [
        {"dep": _T1, "missing": ["status"], "available": ["body", "title"]}
    ]


def test_pure_sequence_dependency_also_passes_with_observation():
    """纯序依赖（depends_on 无 consumes）：produces 未兑现同样放行 + 留痕。"""
    row = _t2_row()
    reason, _ = sc.gate(
        row=row,
        terminals={_T1: _t1_terminal()},
        by_id={_T1: _t1_row()},
        prefix_ids=frozenset(),
    )
    assert reason is None
    observed = sc.unfulfilled_produces(
        row=row,
        terminals={_T1: _t1_terminal()},
        by_id={_T1: _t1_row()},
    )
    assert observed == [
        {"dep": _T1, "missing": ["status"], "available": ["body", "title"]}
    ]


def test_consumed_missing_field_still_blocks():
    """验收②零回归：consumes 引用缺失字段 → 仍拦（判定 2 语义不动）。"""
    reason, detail = sc.gate(
        row=_t2_row(consumes={_T1: ["title", "status"]}),
        terminals={_T1: _t1_terminal()},
        by_id={_T1: _t1_row()},
        prefix_ids=frozenset(),
    )
    assert reason == sc.BLOCKED_CONTRACT_MISSING
    assert "status" in detail
    # 被拦场景不留观察痕（拦截本身已是留痕）
    assert (
        sc.unfulfilled_produces(
            row=_t2_row(consumes={_T1: ["title", "status"]}),
            terminals={_T1: _t1_terminal()},
            by_id={_T1: _t1_row()},
        )
        == []
    )


def test_prefix_dep_unfulfilled_produces_not_misclassified():
    """验收②零回归：前驱在不可变前缀内、produces 未兑现但未被消费 → 放行，
    不得误判 prefix_touch_required（consumes 缺字段落前缀才交人）。"""
    row = _t2_row(consumes={_T1: ["title"]})
    reason, _ = sc.gate(
        row=row,
        terminals={_T1: _t1_terminal()},
        by_id={_T1: _t1_row()},
        prefix_ids=frozenset({_T1}),
    )
    assert reason is None
    observed = sc.unfulfilled_produces(
        row=row,
        terminals={_T1: _t1_terminal()},
        by_id={_T1: _t1_row()},
    )
    assert [o["missing"] for o in observed] == [["status"]]


def test_no_observation_when_produces_fulfilled_or_undeclared():
    """反向对照：produces 全兑现 / 未声明 / 产出非 dict ⇒ 无观察项。"""
    fulfilled = {
        "id": _T1,
        "subtask_id": _T1,
        "type": "tool",
        "output": {"title": "t", "body": "b", "status": "open"},
    }
    row = _t2_row()
    assert (
        sc.unfulfilled_produces(
            row=row, terminals={_T1: fulfilled}, by_id={_T1: _t1_row()}
        )
        == []
    )
    # 未声明 produces
    assert (
        sc.unfulfilled_produces(
            row=row,
            terminals={_T1: _t1_terminal()},
            by_id={_T1: {**_t1_row(), "produces": []}},
        )
        == []
    )
    # 产出是自由文本 ⇒ 不可校验，不替模型猜
    free_text = {"id": _T1, "subtask_id": _T1, "type": "rag", "output": "一段答案"}
    assert (
        sc.unfulfilled_produces(
            row=row, terminals={_T1: free_text}, by_id={_T1: _t1_row()}
        )
        == []
    )


async def test_join_dispatches_and_records_span_observation():
    """编排层闭环：t2 照常派发，且观察留痕写进 span metadata（既有通道）。"""
    plan = [_t1_row(), _t2_row(consumes={_T1: ["title", "body"]})]
    state = {
        "subtasks": plan,
        "subtask_results": [_t1_terminal()],
        "inflight_subtask_ids": [_T1],
        "supervisor_step_count": 1,
    }
    recorded: list[dict] = []
    with patch.object(nodes, "_record_span_metadata", lambda meta: recorded.append(meta)):
        out = await _join_subtasks(state)
    assert _T2 in out["inflight_subtask_ids"], "收窄后 t2 须照常派发"
    assert "subtask_results" not in out, "收窄后不得再写被拦终态"
    observations = [
        meta["step_contract_produces_unfulfilled"]
        for meta in recorded
        if "step_contract_produces_unfulfilled" in meta
    ]
    assert observations, "放行时未兑现的 produces 须写 span 观察留痕"
    flat = [item for batch in observations for item in batch]
    assert {
        "subtask_id": _T2,
        "dep": _T1,
        "missing": ["status"],
        "available": ["body", "title"],
    } in flat


async def test_join_no_observation_span_when_fulfilled():
    """反向对照（编排层）：produces 全兑现 ⇒ 不写观察 span（主路径零 diff）。"""
    plan = [_t1_row(), _t2_row(consumes={_T1: ["title", "body"]})]
    fulfilled = {
        "id": _T1,
        "subtask_id": _T1,
        "type": "tool",
        "output": {"title": "t", "body": "b", "status": "open"},
    }
    state = {
        "subtasks": plan,
        "subtask_results": [fulfilled],
        "inflight_subtask_ids": [_T1],
        "supervisor_step_count": 1,
    }
    recorded: list[dict] = []
    with patch.object(nodes, "_record_span_metadata", lambda meta: recorded.append(meta)):
        out = await _join_subtasks(state)
    assert _T2 in out["inflight_subtask_ids"]
    assert all("step_contract_produces_unfulfilled" not in meta for meta in recorded)

