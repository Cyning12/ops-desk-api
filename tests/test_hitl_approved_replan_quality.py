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

TC2（单测组 · FP-3 反面 + 边界口径）：

- approved 步无同 canonical 成功终态 → 正常消费派发（护栏不误伤批准步，
  FP-3 反面）；
- 同 tool 异 args 不算孪生（canonical 区分），正常派发；
- error 终态不算成功：失败 write 重跑系既有语义，护栏不拦；
- 同批双胞胎：首发照派 · 次发本轮挂起 → 下一 join pass 见终态后
  guard-skip（join 同轮重入结构前提）；
- delegation off 模式零介入（承 off 零 diff 先例）；
- 空保号集合注入段为空串；_guard_write_key canonical 确定性
  （sort_keys 键序无关 / 异参不同键 / 未注册 tool 返 None）。

两枚 TC1 对现码均 RED（护栏/注入未实现）——红测先行时序证据见 git 历史。

N1 收口追加组（task hitl-n1-locked-branch-inject）：

- **TC1-N1** locked 空 + preserved 非空（40 run1 实证形态）：supervisor 重规划
  prompt 须注入保号行名单（现码 else 分支走基础 prompt 不注入 · RED 先行 →
  方案 A `if locked or preserved` 复用 suffix 注入面转 GREEN）。
- **TC2-b** locked 空 + preserved 空（首次规划主路径 · FP-3 钉死）：
  system_content 对基础模板渲染逐字节零 diff。
"""

from __future__ import annotations

import logging
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ops.capability import delegation as dl
from app.ops.lg_rag.multi.nodes import (
    _build_supervisor_system,
    _format_capability_catalog,
    _format_preserved_block,
    _guard_write_key,
    _join_subtasks,
    supervisor_node,
)
from tests.test_hitl_approval_consumption import (  # 承 TB 组罐头/fixture
    _CAPS_PATCH,
    _PLAN_PATCH,
    _TESTING_CAP,
    _approved_req,
    _fake_caps,
    _guard_row,
    _guard_state,
    _new_step_suffix,
    cap_env,  # noqa: F401 - pytest fixture 注入（形参同名由 def 行 noqa F811 承接）
)

_GUARD_LOGGER = "app.ops.lg_rag.multi.nodes"


@pytest.mark.asyncio
async def test_tc1_write_twin_guard_skips_redispatch(cap_env, monkeypatch, caplog):  # noqa: F811
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
    batch = list(joined.get("subtask_results") or [])
    twin = next((r for r in batch if str(r.get("subtask_id")) == s2), None)
    assert twin is not None, "write 孪生须落 guard-skip 终态（现码无任何终态）"
    assert twin.get("write_replay_guard_skip") is True
    assert twin.get("replay_of") == s1
    assert twin.get("output") == {"echo": "W1-OK"}  # 已批准写结果照抄
    assert "error" not in twin
    # 台账面：guard 动作留痕；:2 审批单据不被消费（guard 先于签发检查）
    assert any("write_replay_guard_skip" in r.message for r in caplog.records)
    assert not any(
        "delegation_approval_consumed" in r.message and s2 in r.message for r in caplog.records
    )


@pytest.mark.asyncio
async def test_tc1_supervisor_replan_prompt_sees_preserved_and_results(cap_env):  # noqa: F811
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
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: provider):
        out = await supervisor_node(state)

    system_prompt = str(complete.await_args.args[0][0].content)
    # ① 保号行对 LLM 可见（现码 RED：prompt 只见 locked 前缀，s2 不出现）
    assert s2 in system_prompt, "保号行（approved 待重跑）须注入 replan prompt"
    # ② 已完成步终态结果摘要可见（现码 RED：前缀只给 id/type/input/tool）
    assert "W1-OK" in system_prompt, "locked 前缀终态 output 摘要须注入 replan prompt"
    # 保号契约零 diff：落位仍 locked → 保号行 → LLM 新后缀
    new_id = run_id + ":3"
    assert [r["subtask_id"] for r in out["subtasks"]] == [s1, s2, new_id]


@pytest.mark.asyncio
async def test_tc1_locked_empty_preserved_injected_into_prompt(cap_env):  # noqa: F811
    """TC1-N1（红测先行 · N1 缺口同形签名）：locked 空 + preserved 非空 → 保号行注入。

    场景钉 40 run1 实证形态：hitl 批准单步写，被批准步经 _apply_hitl_decision
    剪结果后无终态、locked 前缀为空，preserved 非空。现码 else 分支走
    _build_supervisor_system 基础 prompt，保号行名单不注入（LLM 仍盲）。
    修复后（方案 A 复用 suffix 注入面）prompt 须含保号行 sid + 钉死措辞；
    保号落位契约零 diff：[保号行, LLM 新后缀]。
    """
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1 = run_id + ":1"
    state = _guard_state(
        run_id,
        [_guard_row(s1, input={"request_id": "r-n1", "note": "批准重跑我"})],
        [],
        hitl_unlocked_ids=[s1],
    )
    complete = AsyncMock(return_value=_new_step_suffix("后续步骤"))
    provider = SimpleNamespace(complete=complete)
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: provider):
        out = await supervisor_node(state)

    system_prompt = str(complete.await_args.args[0][0].content)
    # 现码 RED：locked 空走基础 prompt，s1 不出现（N1 缺口同形签名）
    assert s1 in system_prompt, "locked 空分支保号行（approved 待重跑）须注入 prompt"
    assert "切勿为同一目的再规划新步骤或孪生步骤" in system_prompt
    # 保号落位契约零 diff：locked 空 → [保号行, LLM 新后缀]（seq=1 ⇒ 新 id :2）
    new_id = run_id + ":2"
    assert [r["subtask_id"] for r in out["subtasks"]] == [s1, new_id]


@pytest.mark.asyncio
async def test_tc2_locked_empty_preserved_empty_prompt_zero_diff(cap_env):  # noqa: F811
    """TC2-b（FP-3 钉死）：locked 空 + preserved 空（首次规划主路径）逐字节零 diff。

    preserved 空时 system_content 必须仍是基础模板渲染结果——对 master
    同输入逐字节零 diff，防「顺手统一分支」误伤首次规划主路径。
    """
    run_id = "run-" + uuid.uuid4().hex[:8]
    state = _guard_state(run_id, [], [])
    complete = AsyncMock(return_value=_new_step_suffix("首步"))
    provider = SimpleNamespace(complete=complete)
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: provider):
        await supervisor_node(state)

    system_prompt = str(complete.await_args.args[0][0].content)
    expected = _build_supervisor_system(_format_capability_catalog(_fake_caps()))
    assert system_prompt == expected, "preserved 空主路径须对基础模板逐字节零 diff"
    assert "切勿为同一目的再规划新步骤或孪生步骤" not in system_prompt


@pytest.mark.asyncio
async def test_tc2_guard_does_not_block_approved_step_without_prior_terminal(
    cap_env,  # noqa: F811
    monkeypatch,
    caplog,
):
    """FP-3 反面：approved 步无同 canonical 成功终态 → 正常消费派发。

    护栏只拦「已有异 sid 成功终态」的孪生；批准步自身旧结果已被剪掉
    （无终态可命中），必须照常走消费门放行——误伤批准步即 FP-3 回归。
    """
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1 = run_id + ":1"
    state = _guard_state(run_id, [_guard_row(s1)], [], hitl_unlocked_ids=[s1])
    await cap_env.acreate(_approved_req(run_id, s1))

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    assert s1 in (joined.get("inflight_subtask_ids") or [])
    assert any(
        "delegation_approval_consumed" in r.message and s1 in r.message for r in caplog.records
    )
    assert not any("write_replay_guard_skip" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_tc2_guard_does_not_block_different_args(cap_env, monkeypatch):  # noqa: F811
    """canonical 区分：同 tool 异 args 不是孪生 → 正常消费派发。"""
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1, s2 = run_id + ":1", run_id + ":2"
    state = _guard_state(
        run_id,
        [
            _guard_row(s1, input={"request_id": "r-x", "note": "甲"}),
            _guard_row(s2, input={"request_id": "r-x", "note": "乙"}),
        ],
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

    joined = await _join_subtasks(state)

    assert s2 in (joined.get("inflight_subtask_ids") or [])
    batch = list(joined.get("subtask_results") or [])
    assert not any(
        str(r.get("subtask_id")) == s2 and r.get("write_replay_guard_skip") for r in batch
    )


@pytest.mark.asyncio
async def test_tc2_guard_does_not_block_retry_after_failed_write(cap_env, monkeypatch):  # noqa: F811
    """error 终态不算成功终态：失败 write 的重跑是既有语义，护栏不拦。"""
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1, s2 = run_id + ":1", run_id + ":2"
    args = {"request_id": "r-fail", "note": "首发失败"}
    state = _guard_state(
        run_id,
        [_guard_row(s1, input=args), _guard_row(s2, input=dict(args))],
        [
            {
                "subtask_id": s1,
                "id": s1,
                "type": "tool",
                "tool": _TESTING_CAP,
                "error": "adapter boom",
            }
        ],
        plan_prefix_ids=[s1],
        hitl_unlocked_ids=[s2],
    )
    await cap_env.acreate(_approved_req(run_id, s2))

    joined = await _join_subtasks(state)

    assert s2 in (joined.get("inflight_subtask_ids") or [])


@pytest.mark.asyncio
async def test_tc2_intra_batch_twins_deferred_then_guard_skipped(cap_env, monkeypatch):  # noqa: F811
    """同批双胞胎：首发照派 · 次发本轮挂起 → 下一 join pass guard-skip。

    结构前提：subtask_join 同轮重入（graph.py:94-103 workers 回 join）。
    次发挂起须「不派发 · 不落任何终态」（等首发终态出现再照抄）。
    """
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1, s2 = run_id + ":1", run_id + ":2"
    args = {"request_id": "r-batch", "note": "同批双胞胎"}
    rows = [_guard_row(s1, input=args), _guard_row(s2, input=dict(args))]
    # 只有首发持票；次发无票——若挂起逻辑漏到签发检查，次发会被 HITL 拦
    state1 = _guard_state(run_id, rows, [])
    await cap_env.acreate(_approved_req(run_id, s1))

    joined1 = await _join_subtasks(state1)

    assert (joined1.get("inflight_subtask_ids") or []) == [s1]
    batch1 = list(joined1.get("subtask_results") or [])
    assert not any(str(r.get("subtask_id")) == s2 for r in batch1), (
        "次发本轮挂起：不落终态（含 blocked）"
    )

    # 下一 join pass：首发已成功终态 → 次发 guard-skip 照抄
    state2 = _guard_state(
        run_id,
        rows,
        [
            {
                "subtask_id": s1,
                "id": s1,
                "type": "tool",
                "tool": _TESTING_CAP,
                "output": {"echo": "W1-OK"},
            }
        ],
        hitl_unlocked_ids=[s2],
    )
    joined2 = await _join_subtasks(state2)

    assert (joined2.get("inflight_subtask_ids") or []) == []
    batch2 = list(joined2.get("subtask_results") or [])
    twin = next(r for r in batch2 if str(r.get("subtask_id")) == s2)
    assert twin.get("write_replay_guard_skip") is True
    assert twin.get("replay_of") == s1
    assert twin.get("output") == {"echo": "W1-OK"}


@pytest.mark.asyncio
async def test_tc2_guard_zero_touch_when_delegation_off(cap_env, monkeypatch, caplog):  # noqa: F811
    """off 模式零介入先例：护栏整段不触达，孪生照常派发（无签发拦截）。"""
    monkeypatch.setenv(dl.ENV_MODE, "off")
    run_id = "run-" + uuid.uuid4().hex[:8]
    s1, s2 = run_id + ":1", run_id + ":2"
    args = {"request_id": "r-off", "note": "off 零 diff"}
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

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    assert s2 in (joined.get("inflight_subtask_ids") or [])
    batch = list(joined.get("subtask_results") or [])
    assert not any(r.get("write_replay_guard_skip") for r in batch)
    assert not any("write_replay_guard_skip" in r.message for r in caplog.records)


def test_tc2_guard_write_key_canonical_and_preserved_block_empty(cap_env):  # noqa: F811
    """canonical 确定性 + 空保号集合零 diff（TB4 五键总闸的注入侧语义）。"""
    assert _guard_write_key(_guard_row("run:1", input={"b": 1, "a": 2})) == _guard_write_key(
        _guard_row("run:2", input={"a": 2, "b": 1})
    )
    assert _guard_write_key(_guard_row("run:3", input={"a": 2, "b": 3})) != _guard_write_key(
        _guard_row("run:4", input={"a": 2, "b": 1})
    )
    # 未注册 tool / 非 tool 行 / 空载荷 → None（护栏是优化不是闸门）
    assert _guard_write_key(_guard_row("run:5", tool="unregistered.tool")) is None
    assert _guard_write_key({"subtask_id": "run:6", "type": "rag", "input": "x"}) is None
    # 空保号集合注入段为空串——模板 $preserved_block 槽退化为空行
    assert _format_preserved_block([]) == ""
    assert _format_preserved_block(None) == ""
