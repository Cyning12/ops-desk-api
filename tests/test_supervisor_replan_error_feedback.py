"""supervisor-replan-error-feedback：重规划错误反哺验收。

契约锚：docs/tasks/active/task_supervisor_replan_error_feedback.md
（实测 run cb25483697624aafbb1cf864015c3b10：write 步 consumes 声明错字段名
被契约闸拦 contract_missing_field——声明 [title,body,status]，前驱实际字段
state——重规划 prompt 零错误信息，两轮原样照抄同一错误声明后 budget_exhausted。
修复：第一轮的错误必须反哺第二轮）。

- **TC1**（验收①·spy prompt）：第二轮重规划 prompt 含失败原因行
  （「→ 失败：contract_missing_field：…」）+ 前驱实际可用字段清单
  （「实际产出字段 [...]」）——把「猜字段名」变成「从清单选字段名」。
- **TC2**（验收②·收敛验证）：run cb2548 同形场景——consumes 声明错字段名
  第一轮被拦且 detail 携带可用字段清单；重规划后 consumes 收敛到真实
  字段名 → 契约闸放行派发（端到端实测由评测另做，此处验证 prompt 输入
  充分 + 收敛后闸门确实放行，单测层面闭环）。
- **TC3**（A 层纯单元）：失败行格式钉死（400 截断、blocked_by 缺失退化
  「→ 失败：{error}」不伪造空段）；failed 为空输出与 master 逐字节一致。
- **TC4**（验收③·零 diff 钉死，沿用 preserved_block 的 FP 先例口径）：
  重规划路径无失败步时 system prompt 对 master 二参渲染逐字节零 diff。
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.ops.capability import delegation as dl
from app.ops.lg_rag.multi import step_contract as sc
from app.ops.lg_rag.multi.nodes import (
    MAX_SUBTASKS,
    _build_supervisor_suffix_system,
    _format_capability_catalog,
    _format_prefix_block,
    _join_subtasks,
    supervisor_node,
)
from tests.test_hitl_approval_consumption import (  # 承 TB 组罐头/fixture
    _CAPS_PATCH,
    _PLAN_PATCH,
    _TESTING_CAP,
    _fake_caps,
    _guard_state,
    _new_step_suffix,
    cap_env,  # noqa: F401 - pytest fixture 注入
)

_S1_OUTPUT = {"number": "INC-001", "title": "网络故障", "state": "open", "body": "已受理"}
_AVAILABLE_FIELDS = "['body', 'number', 'state', 'title']"  # sorted 后字面


def _cb2548_rows(run_id: str) -> tuple[dict, dict]:
    """run cb2548 同形计划行：s1 建工单成功；s2 写步 consumes 声明错字段名。

    s2 声明 consumes=[status]，而 s1 实际产出字段是 state——契约闸必拦。
    """
    s1, s2 = run_id + ":1", run_id + ":2"
    row_s1 = {
        "id": s1,
        "subtask_id": s1,
        "alias": "t1",
        "type": "tool",
        "tool": _TESTING_CAP,
        "input": {"request_id": "r-ticket", "note": "建工单"},
        "depends_on": [],
        "produces": ["number", "state", "title"],
    }
    row_s2 = {
        "id": s2,
        "subtask_id": s2,
        "alias": "t2",
        "type": "tool",
        "tool": _TESTING_CAP,
        "input": {"request_id": "r-notify", "note": "按工单状态发通知"},
        "depends_on": [s1],
        "consumes_resolved": {s1: ["status"]},  # cb2548 错字段名（真实字段是 state）
    }
    return row_s1, row_s2


def _s1_success_terminal(sid: str) -> dict:
    return {
        "subtask_id": sid,
        "id": sid,
        "type": "tool",
        "tool": _TESTING_CAP,
        "output": dict(_S1_OUTPUT),
    }


def _blocked_terminal(row: dict, reason: str, detail: str) -> dict:
    """镜像 nodes.py 被拦终态组装（_error_terminal + blocked_by 留痕）。"""
    return {
        "id": row["subtask_id"],
        "subtask_id": row["subtask_id"],
        "type": row["type"],
        "input": str(row.get("input") or ""),
        "error": f"{sc.label_of(reason)}（{detail}）",
        "blocked_by": reason,
    }


async def test_tc1_replan_prompt_contains_failure_reason_and_available_fields(cap_env):  # noqa: F811
    """TC1（验收①）：第二轮重规划 prompt 含失败原因行 + 前驱可用字段清单。

    被拦终态由真实 sc.gate 产出（非手拼 detail）——验证「闸 detail 增强 →
    错误终态 → 失败行进 prompt」整条链路闭环，而非只测格式函数。
    """
    run_id = "run-" + uuid.uuid4().hex[:8]
    row_s1, row_s2 = _cb2548_rows(run_id)
    s1, s2 = row_s1["subtask_id"], row_s2["subtask_id"]
    # 真实闸产出被拦终态（cb2548：s1 非不可变前缀 ⇒ contract_missing_field）
    reason, detail = sc.gate(
        row=row_s2,
        terminals={s1: _s1_success_terminal(s1)},
        by_id={s1: row_s1, s2: row_s2},
        prefix_ids=frozenset(),
    )
    assert reason == sc.BLOCKED_CONTRACT_MISSING
    state = _guard_state(
        run_id,
        [row_s1, row_s2],
        [_s1_success_terminal(s1), _blocked_terminal(row_s2, reason, detail)],
    )
    complete = AsyncMock(return_value=_new_step_suffix("修正 consumes 后重发"))
    provider = SimpleNamespace(complete=complete)
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: provider):
        await supervisor_node(state)

    system_prompt = str(complete.await_args.args[0][0].content)
    # ① 失败原因行（A 层）：被拦步对模型可见 + 拦截码 + 死因
    #    （失败行与锁定行同格式，以 alias 指代——模型重规划时换新 id）
    assert "- t2（tool）：" in system_prompt, (
        "被拦步须出现在重规划 prompt（现码失败步完全不可见）"
    )
    assert "→ 失败：contract_missing_field：" in system_prompt, (
        "失败摘要行须含拦截码（模型须知道这步死了、死因是什么）"
    )
    assert "切勿原样照抄上一轮的 consumes/produces 声明" in system_prompt
    # ② 前驱实际可用字段清单（B 层）：从「猜字段名」变「从清单选字段名」
    assert f"实际产出字段 {_AVAILABLE_FIELDS}" in system_prompt, (
        "重规划 prompt 须含前驱实际可用字段清单（sorted keys）"
    )
    assert "声明的字段不存在" in system_prompt
    assert "['status']" in system_prompt  # 声明的错字段名可见（供对照修正）
    # 既有注入面无回归：locked 前缀终态摘要仍在
    assert "INC-001" in system_prompt


async def test_tc2_consumes_converges_to_real_fields_gate_passes(cap_env, monkeypatch):  # noqa: F811
    """TC2（验收②·单测层面闭环）：consumes 收敛到真实字段名后契约闸放行。

    第一轮：cb2548 同形错声明 → 拦截且 detail 携带可用字段清单（纠错回路
    的 prompt 输入充分性）；第二轮：模型按清单收敛 consumes → 闸放行派发。
    委派签发面关 off 聚焦契约闸（审批回路非本 task 验收面）。
    """
    monkeypatch.setenv(dl.ENV_MODE, dl.MODE_OFF)
    run_id = "run-" + uuid.uuid4().hex[:8]
    row_s1, row_s2 = _cb2548_rows(run_id)
    s1, s2 = row_s1["subtask_id"], row_s2["subtask_id"]

    # 第一轮：consumes 声明错字段名 → 契约闸拦截，detail 携带可用字段清单
    state1 = _guard_state(
        run_id, [row_s1, row_s2], [_s1_success_terminal(s1)], plan_prefix_ids=[]
    )
    joined1 = await _join_subtasks(state1)
    batch1 = list(joined1.get("subtask_results") or [])
    blocked = next((r for r in batch1 if str(r.get("subtask_id")) == s2), None)
    assert blocked is not None, "错字段名声明须被契约闸拦截"
    assert blocked.get("blocked_by") == sc.BLOCKED_CONTRACT_MISSING
    error_text = str(blocked.get("error") or "")
    assert f"实际产出字段 {_AVAILABLE_FIELDS}" in error_text, (
        "拦截 detail 须携带前驱实际可用字段清单（反哺重规划的原料）"
    )
    assert "['status']" in error_text  # 声明的缺失字段
    assert s2 not in (joined1.get("inflight_subtask_ids") or [])

    # 第二轮：consumes 收敛到真实字段名（从清单选）→ 闸放行派发
    row_s2_fixed = dict(row_s2, consumes_resolved={s1: ["state", "title"]})
    state2 = _guard_state(
        run_id, [row_s1, row_s2_fixed], [_s1_success_terminal(s1)], plan_prefix_ids=[]
    )
    joined2 = await _join_subtasks(state2)
    assert s2 in (joined2.get("inflight_subtask_ids") or []), (
        "consumes 收敛到真实字段名后契约闸须放行"
    )
    batch2 = list(joined2.get("subtask_results") or [])
    assert not any(str(r.get("subtask_id")) == s2 and "error" in r for r in batch2)


def test_tc3_prefix_block_failure_line_format_and_empty_failed_zero_diff():
    """TC3（A 层纯单元）：失败行格式钉死 + failed 为空逐字节零 diff。"""
    locked_row = {
        "subtask_id": "run-x:1",
        "alias": "t1",
        "type": "tool",
        "tool": "testing.write.echo",
        "input": {"k": "v"},
    }
    terms = {"run-x:1": {"output": {"echo": "ok"}}}
    expected_base = (
        "- t1（tool）：{'k': 'v'} [tool=testing.write.echo]\n"
        '  → 终态结果：{"echo": "ok"}'
    )
    # 锁定行渲染对 master 逐字节钉死（既有格式回归锚）
    assert _format_prefix_block([locked_row], terms) == expected_base
    # failed 为空 ⇒ 与二参（master 形态）调用逐字节一致（主路径零 diff）
    assert _format_prefix_block([locked_row], terms, failed=[]) == expected_base
    assert _format_prefix_block([locked_row], terms, failed=None) == expected_base

    # 失败行：blocked_by + error；超 400 截断补省略号（纠错信息须存活）
    frow = {
        "subtask_id": "run-x:2",
        "alias": "t2",
        "type": "tool",
        "tool": "testing.write.echo",
        "input": "发通知",
    }
    long_error = "x" * 500
    terms2 = {**terms, "run-x:2": {"error": long_error, "blocked_by": "contract_missing_field"}}
    out = _format_prefix_block([locked_row], terms2, failed=[frow])
    assert out.split("\n")[0] == expected_base.split("\n")[0]  # 锁定行不被污染
    assert "以下步骤上一轮执行失败（未锁定，需在新后缀中修正声明后重新规划；" in out
    fail_line = (
        "- t2（tool）：发通知 [tool=testing.write.echo]\n"
        "  → 失败：contract_missing_field：" + "x" * 400 + "…(截断)"
    )
    assert fail_line in out

    # blocked_by 缺失（工人失败等无拦截码形态）⇒ 退化「→ 失败：{error}」
    out3 = _format_prefix_block([], {"run-x:2": {"error": "boom"}}, failed=[frow])
    assert "→ 失败：boom" in out3
    assert "→ 失败：：" not in out3, "blocked_by 缺失不得伪造空段"


async def test_tc4_replan_prompt_zero_diff_without_failed_steps(cap_env):  # noqa: F811
    """TC4（验收③·FP 钉死，沿用 preserved_block 先例口径）：无失败步零 diff。

    重规划路径（locked 非空）但无任何失败终态步时，system prompt 必须
    与 master 二参渲染逐字节一致——失败段是纯加法，不得污染主路径。
    """
    run_id = "run-" + uuid.uuid4().hex[:8]
    row_s1, _ = _cb2548_rows(run_id)
    s1 = row_s1["subtask_id"]
    state = _guard_state(run_id, [row_s1], [_s1_success_terminal(s1)])
    complete = AsyncMock(return_value=_new_step_suffix("后续步骤"))
    provider = SimpleNamespace(complete=complete)
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: provider):
        await supervisor_node(state)

    system_prompt = str(complete.await_args.args[0][0].content)
    expected = _build_supervisor_suffix_system(
        _format_capability_catalog(_fake_caps()),
        _format_prefix_block([dict(row_s1)], {s1: _s1_success_terminal(s1)}),  # master 二参形态
        MAX_SUBTASKS - 1,
        preserved_block="",
    )
    assert system_prompt == expected, "无失败步重规划 prompt 须对 master 逐字节零 diff"
    assert "→ 失败" not in system_prompt
