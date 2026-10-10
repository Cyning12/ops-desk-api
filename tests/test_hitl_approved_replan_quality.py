"""hitl-approved-replan-quality：approved resume 后定点重跑 + write 零重放验收。

契约锚：docs/tasks/active/task_hitl_approved_replan_quality.md（SPEC §9 序1）。

TC1（红测先行 · D1=C 混合案行为断言）：

- **TC1-a** write 孪生步结构护栏：locked 前缀已有同 (tool,args) write 成功
  终态时，replan 后 approved 待重跑步（异 sid）在 _join_subtasks 分发层被
  guard-skip —— 不派发、不消费审批单据，写成功终态 output 照抄 +
  write_replay_guard_skip / replay_of 台账（契约一：write 零重发，结构性）。
- **TC1-b** replan 注入去盲：supervisor 重规划 prompt 须让 LLM 看见
  ①保号行（approved 待重跑步）②已完成步终态结果摘要（破「LLM 不知晓
  保号行」盲循环，SPEC §9 序1 现象①）。

两枚对现码均 RED（护栏/注入未实现）——红测先行时序证据见 git 历史。
"""

from __future__ import annotations

import logging
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ops.lg_rag.multi.nodes import _join_subtasks, supervisor_node
from tests.test_hitl_approval_consumption import (  # 承 TB 组罐头/fixture
    _CAPS_PATCH,
    _PLAN_PATCH,
    _TESTING_CAP,
    _approved_req,
    _fake_caps,
    _guard_row,
    _guard_state,
    _new_step_suffix,
    cap_env,
)

_GUARD_LOGGER = "app.ops.lg_rag.multi.nodes"


@pytest.mark.asyncio
async def test_tc1_write_twin_guard_skips_redispatch(cap_env, monkeypatch, caplog):
    """TC1-a：write 孪生步（异 sid · 同 tool+args）guard-skip 零重放。

    场景钉 live 签名：:1 write 已成功终态（locked 前缀）；:2 为 approved
    unlocked 待重跑步且与 :1 canonical 相同。即便 :2 持新鲜 approved 单据
    （消费门本可放行），分发层护栏必须先于签发检查拦下：不派发、不消费，
    落 guard-skip 成功终态（output 照抄 :1）。FP-3 反面由 TC2 组覆盖。
    """
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1, s2 = run_id + ":1", run_id + ":2"
    args = {"request_id": "r-twin", "note": "同参写步"}
    state = _guard_state(
        run_id,
        [_guard_row(s1, input=args), _guard_row(s2, input=dict(args))],
        [
            {
                "subtask_id": s1,
                "id": s1,
                "type": "tool",
                "tool": _TESTING_CAP,
                "output": {"echo": "W1-OK"},
            }
        ],
        plan_prefix_ids=[s1],
        hitl_unlocked_ids=[s2],
    )
    await cap_env.acreate(_approved_req(run_id, s2))

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    # 现码 RED：消费命中放行 → inflight 含 s2（write 二次执行即重放危害）
    assert s2 not in (joined.get("inflight_subtask_ids") or []), (
        "write 孪生步不得派发（现码消费放行派发）"
    )
    batch = [r for r in (joined.get("subtask_results") or [])]
    twin = next((r for r in batch if str(r.get("subtask_id")) == s2), None)
    assert twin is not None, "write 孪生须落 guard-skip 终态（现码无任何终态）"
    assert twin.get("write_replay_guard_skip") is True
    assert twin.get("replay_of") == s1
    assert twin.get("output") == {"echo": "W1-OK"}  # 已批准写结果照抄
    assert "error" not in twin
    # 台账面：guard 动作留痕；:2 审批单据不被消费（guard 先于签发检查）
    assert any("write_replay_guard_skip" in r.message for r in caplog.records)
    assert not any(
        "delegation_approval_consumed" in r.message and s2 in r.message
        for r in caplog.records
    )


@pytest.mark.asyncio
async def test_tc1_supervisor_replan_prompt_sees_preserved_and_results(cap_env):
    """TC1-b：replan prompt 注入保号行 + 已完成步终态结果摘要（去盲）。

    SPEC §9 序1 现象①：LLM 不知晓保号行 → 重规划同语义写步孪生。注入后
    system prompt 须含 ①保号行 sid ②locked 前缀步的终态 output 摘要。
    保号落位契约（TB1 组）不动：[s1, s2, 新盖章 :3]。
    """
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1, s2 = run_id + ":1", run_id + ":2"
    state = _guard_state(
        run_id,
        [_guard_row(s1), _guard_row(s2, input={"request_id": "r-2", "note": "重跑我"})],
        [
            {
                "subtask_id": s1,
                "id": s1,
                "type": "tool",
                "tool": _TESTING_CAP,
                "output": {"echo": "W1-OK"},
            }
        ],
        plan_prefix_ids=[s1],
        hitl_unlocked_ids=[s2],
    )
    complete = AsyncMock(return_value=_new_step_suffix("后续步骤"))
    provider = SimpleNamespace(complete=complete)
    with patch(_CAPS_PATCH, new=_fake_caps), patch(
        _PLAN_PATCH, new=lambda *a, **k: provider
    ):
        out = await supervisor_node(state)

    system_prompt = str(complete.await_args.args[0][0].content)
    # ① 保号行对 LLM 可见（现码 RED：prompt 只见 locked 前缀，s2 不出现）
    assert s2 in system_prompt, "保号行（approved 待重跑）须注入 replan prompt"
    # ② 已完成步终态结果摘要可见（现码 RED：前缀只给 id/type/input/tool）
    assert "W1-OK" in system_prompt, "locked 前缀终态 output 摘要须注入 replan prompt"
    # 保号契约零 diff：落位仍 locked → 保号行 → LLM 新后缀
    new_id = run_id + ":3"
    assert [r["subtask_id"] for r in out["subtasks"]] == [s1, s2, new_id]
