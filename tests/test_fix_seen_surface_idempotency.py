"""fix-seen-surface-idempotency：reset seen 面后首轮巡检不重复拉起存量 write ticket。

缺陷（issue #335 · 维护者 comment `6668554143` / 30 授权 `6669768156`）：
worker 重启后 seen 面重置无幂等守卫，首次巡检重复拉起存量 write ticket，
触发 overlap_warning 噪音。

探针定位（30 红测先行 · 真派发路径）：
- **seen 面 = 进程内「本轮已见/已带回」去重面**——具体承载 =
  ``_persist_hitl`` 的 ``already``（state ``hitl_requests`` 面）；
  observe 挂起时节点 return 值不进 checkpoint（nodes.py:2197 既有注释），
  重启后 state 重建 ⇒ ``hitl_requests`` 必然为空 ⇒ seen 面归零；
  库面存量单据（T1）仍在。
- **重复拉起路径**：重启后首轮巡检走 supervisor 重规划（reset 后无
  locked/preserved 保号面）→ LLM 对同一写意图产出**新 sid 孪生步**
  （replay-guard 文档化形态：「LLM 不知晓保号行 → 重规划同语义写步孪生」）→
  ``_join_subtasks`` 真派发孪生步 → 写闸 fail-closed 再拦
  （`_write_execution_approval` 三元组**精确 sid 匹配** · T1 挂 A ⇒ B 不命中）
  → ``_persist_hitl`` 建单侧去重**只认精确 sid**（store pending 面 T1=sid A
  对孪生 B 不可见 · ``_approved_fresh_for_subtask`` 同精确 sid）⇒ **新建 T2**
  = 同一写意图同 run 库面两单（重叠噪音源）。
- 既有 write 孪生重放护栏（``write_replay_guard_skip``）只索引**成功终态**，
  被拦/未执行步不在索引面 ⇒ 本缺陷形态不在其护栏面（探针实证见对拍组）。

修复语义（设计闸决策点①裁决 · 引用 issue #335 comment `6669768156` ·
决策点② = status/seen_surface 双条件位）：（待 30 实现回填）

验收映射（维护者 30 授权六条件 · issue #335 comment `6669768156`）：

- **负样本（红线）**：reset seen 面 → 首轮巡检（真 join/写闸/persist 链）→
  存量 write ticket 拉起恰一次（库面同 run 同写意图 live 单恰一笔 · 孪生步
  把存量单带回不新建）且 overlap 拉起噪音台账零新增；
- **常规对拍**：无重置的常规巡检轮次（同 sid 重放 / 无孪生）与修复前零漂移。
"""

from __future__ import annotations

import json
import logging
import uuid
from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _join_subtasks,
    _observe,
    _persist_hitl,
    supervisor_node,
    tool_exec_node,
)
from tests.test_hitl_approval_consumption import (
    _CAPS_PATCH,
    _PLAN_PATCH,
    _TESTING_CAP,
    _fake_caps,
    _llm_returning,
    _observe_graph_factory,
)

_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"

_WRITE_ARGS = {"request_id": "r-1", "note": "demo"}
_PULL_LOG = "capability_write_hitl_required"


@pytest.fixture
def write_env(monkeypatch):
    """写闸面环境：放行 testing tag + 干净 InMemory store（每用例隔离）。"""
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    load_capability_manifest(_TESTING_MANIFEST)
    store = InMemoryHitlStore()
    set_hitl_store(store)
    yield store
    reset_hitl_store()


def _mk(run_id: str, sid: str) -> tuple[dict, dict]:
    """单步写 tool 计划 state（承 delegation/TA 范式）。"""
    state = {
        "messages": [HumanMessage(content="演示写操作审批")],
        "run_id": run_id,
        "user_id": "u-fix",
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": dict(_WRITE_ARGS),
                "tool": _TESTING_CAP,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [],
        "allowed_capability_ids": [_TESTING_CAP],
        "host_subtask_seq": 1,
    }
    return state, state["subtasks"][0]


async def _blocked_round(state: dict, sid: str, store: InMemoryHitlStore, caplog) -> dict:
    """一轮真巡检：join 派发 → tool_exec 写闸拦 → observe → persist 建单。

    返回带 blocked 终态 + 已建单的 merged state（真链形态同 delegation
    负样本：capability_write 闸在 tool_exec 面 · delegation 闸在 join 面）。
    """
    joined = await _join_subtasks(state)
    assert sid in (joined.get("inflight_subtask_ids") or []), "join 应派发该写步"
    row = next(r for r in state["subtasks"] if str(r.get("subtask_id")) == sid)
    exec_out = await tool_exec_node({**state, "assigned_subtask": row})
    term = next(
        (t for t in exec_out["subtask_results"] if str(t.get("subtask_id")) == sid),
        None,
    )
    assert term is not None, "tool_exec 必须落终态"
    assert term.get("blocked_by") == "capability_write_hitl_required"
    merged = {**state, "subtask_results": [term], "inflight_subtask_ids": []}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-probe")
    assert unpersisted is False
    assert len(created) == 1
    return merged


async def _live_write_tickets(store: InMemoryHitlStore, run_id: str) -> list[dict]:
    """该 run 的写闸类 live 单据（pending + approved 全量 · 重叠判据）。"""
    rows = await store.alist(status="pending", limit=500)
    rows += await store.alist(status="approved", limit=500)
    return [
        r
        for r in rows
        if str(r.get("run_id") or "") == run_id
        and str(r.get("blocked_by") or "") == "capability_write_hitl_required"
    ]


def _pull_log_count(caplog) -> int:
    """overlap 拉起噪音台账：全日志中写闸拉起结构化行数（每建单一行）。"""
    return sum(1 for r in caplog.records if _PULL_LOG in r.message)


# ---------------------------------------------------------------------------
# 负样本（维护者红线）：reset seen 面 → 首轮巡检 → 存量 write ticket 拉起恰一次
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_negative_reset_first_round_no_duplicate_write_ticket_pull(
    write_env, monkeypatch, caplog
):
    """reset 后首轮巡检不重复拉起：真链挂起 → checkpoint 重建（seen 面重置）
    → supervisor 重规划孪生（新 sid 同写意图）→ join/写闸/persist 首轮
    → 库面同 run 同写意图 live 单恰一笔（存量 T1 带回 · 零新建）·
    overlap 拉起噪音台账零新增。

    修复前红：孪生步 B 不在 store pending 精确 sid 面 ⇒ 新建 T2 ⇒ 两单。
    """
    store = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid_a = f"{run_id}:1"
    state, _row = _mk(run_id, sid_a)

    # ① 首轮巡检（重启前）：写闸拦下 → 存量票 T1(sid=A) 落库
    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        merged = await _blocked_round(state, sid_a, store, caplog)
    tickets = await _live_write_tickets(store, run_id)
    assert [t["id"] for t in tickets] != []
    assert len(tickets) == 1, f"首轮后应恰一笔存量票：{tickets}"
    t1_id = tickets[0]["id"]
    assert _pull_log_count(caplog) == 1

    # ② worker 重启语义：图真挂起 → checkpoint 重建（新图实例 aget_state）。
    #    seen 面（hitl_requests）属挂起节点 return 值，不进 checkpoint——
    #    重建后必为空（探针前置断言：reset 真实发生）。
    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-probe"}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None, "前置：图没有被挂起"
    fresh_graph = _observe_graph_factory(checkpointer=saver)
    snapshot = await fresh_graph.aget_state({"configurable": {"thread_id": "t-probe"}})
    rebuilt = dict(snapshot.values)
    assert not (rebuilt.get("hitl_requests") or []), (
        "前置：重启重建后 hitl_requests 必为空（seen 面重置 · nodes.py:2197 注释面）"
    )
    assert _run_results_has_blocked(rebuilt, sid_a)

    # ③ 重启后首轮巡检：supervisor 重规划（reset 后无 locked/preserved
    #    保号面）→ LLM 对同一写意图产孪生新步（host 盖章新 sid=B）——
    #    replay-guard 文档化形态（LLM 不知晓保号行 → 孪生）。
    # LLM 计划面 input 必填非空串（_parse_subtasks 钉死）；写意图走 args 通道，
    # 与首轮计划行同 args ⇒ canonical 键一致（真孪生语义）。
    twin_payload = json.dumps(
        {
            "subtasks": [
                {
                    "id": "s1",
                    "type": "tool",
                    "tool": _TESTING_CAP,
                    "input": "demo 写（孪生重规划）",
                    "args": dict(_WRITE_ARGS),
                    "depends_on": [],
                }
            ]
        },
        ensure_ascii=False,
    )
    with (
        patch(_CAPS_PATCH, new=_fake_caps),
        patch(_PLAN_PATCH, new=_llm_returning(twin_payload)),
    ):
        replanned = await supervisor_node(rebuilt)
    twin_row = next(
        r
        for r in replanned["subtasks"]
        if str(r.get("subtask_id") or "") != sid_a
        and str(r.get("tool") or "") == _TESTING_CAP
    )
    sid_b = str(twin_row["subtask_id"])

    # ④ 首轮巡检真链：join——孪生步命中巡检层守卫 ⇒ 继承在途终态（不派发）
    #    → observe → persist（status 位 = 库面同写意图 live 单 · 迁附带回 T1）。
    #    计划面 = 原步 A（checkpoint 存活）+ 孪生步 B（重规划新增）——
    #    「保留原步又加孪生」是重规划的真实输出形态。
    twin_rows = [r for r in replanned["subtasks"] if str(r.get("subtask_id")) != sid_a]
    round2 = {**rebuilt, "subtasks": [*rebuilt["subtasks"], *twin_rows]}
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        joined2 = await _join_subtasks(round2)
        term_b = next(
            (t for t in joined2["subtask_results"] if str(t.get("subtask_id")) == sid_b),
            None,
        )
        assert term_b is not None, "孪生步必须经 join 落到终态（继承在途拦态）"
        assert term_b.get("blocked_by") == "capability_write_hitl_required"
        assert term_b.get("replay_of") == sid_a, "孪生步须继承在途终态并溯源原步"
        assert sid_b not in (joined2.get("inflight_subtask_ids") or []), (
            "守卫生效：孪生步不得重复派发（重复派发 = 重复拉起噪音）"
        )
        assert any(
            "write_ticket_twin_inherited" in r.message for r in caplog.records
        ), "继承动作须留可观测台账"
        # LangGraph 列表合并语义：checkpoint 结果 + 本轮 join 增量
        merged2 = {
            **round2,
            "subtask_results": [
                *(rebuilt.get("subtask_results") or []),
                *list(joined2["subtask_results"]),
            ],
        }
        obs2 = _observe(merged2)
        assert set(obs2["hitl_pending"]) == {sid_a, sid_b}
        created2, unpersisted2 = await _persist_hitl(merged2, obs2, thread_id="t-probe")
    assert unpersisted2 is False

    # ⑤ 红线断言：存量 write ticket 拉起恰一次——同 run 同写意图库面恰一笔
    #    （T1 · 已迁附孪生步）；persist 只能把存量单带回（created2 无新 id）；
    #    overlap 拉起噪音台账零新增（孪生步未派发 ⇒ 写闸拦截行零新增）。
    tickets_after = await _live_write_tickets(store, run_id)
    assert len(tickets_after) == 1, (
        f"reset 后首轮巡检重复拉起存量 write ticket（库面 {len(tickets_after)} 笔 · "
        f"幂等缺口实证）：{[t['id'] for t in tickets_after]}"
    )
    assert tickets_after[0]["id"] == t1_id, "存量票须原单保留（非替换/非新建）"
    assert str(tickets_after[0].get("subtask_id") or "") == sid_b, (
        "存量票连接域迁附孪生步（批准→解锁→消费链路与新建单同义）"
    )
    assert all(str(r.get("id") or "") == t1_id for r in created2), (
        f"孪生步 persist 应只带回存量单 T1：{[r.get('id') for r in created2]}"
    )
    assert _pull_log_count(caplog) == 0, (
        "reset 后首轮巡检不得新增 overlap 拉起噪音（写闸拦截行零新增）"
    )


def _run_results_has_blocked(state: dict, sid: str) -> bool:
    for row in state.get("subtask_results") or []:
        if (
            str(row.get("subtask_id") or "") == sid
            and str(row.get("blocked_by") or "") == "capability_write_hitl_required"
        ):
            return True
    return False


# ---------------------------------------------------------------------------
# 常规对拍：无重置常规轮次 / 同 sid 重放 / 成功孪生护栏面 与修复前零漂移
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_same_sid_repersist_after_reset_attaches_existing(write_env, caplog):
    """对拍①：reset 后同 sid 重放（observe 重跑 · 非孪生形态）——
    store pending 精确 sid 面命中 ⇒ 带回存量单不新建（既有语义零漂移基线）。"""
    store = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, _row = _mk(run_id, sid)
    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        merged = await _blocked_round(state, sid, store, caplog)
        t1_id = (await _live_write_tickets(store, run_id))[0]["id"]

        # 重启语义：挂起 → checkpoint 重建
        saver = InMemorySaver()
        async for _chunk in _observe_graph_factory(checkpointer=saver).astream(
            merged, {"configurable": {"thread_id": "t-probe"}}, stream_mode="updates"
        ):
            pass
        snapshot = await _observe_graph_factory(checkpointer=saver).aget_state(
            {"configurable": {"thread_id": "t-probe"}}
        )
        rebuilt = dict(snapshot.values)

        # 同 sid 重放巡检（observe 重跑 → persist 再入）
        caplog.clear()
        obs = _observe(rebuilt)
        created, _ = await _persist_hitl(rebuilt, obs, thread_id="t-probe")

    assert [str(r.get("id") or "") for r in created] == [t1_id], "同 sid 重放只许带回存量单"
    assert len(await _live_write_tickets(store, run_id)) == 1
    assert _pull_log_count(caplog) == 0


@pytest.mark.asyncio
async def test_success_twin_replay_guard_zero_drift(write_env, monkeypatch, caplog):
    """对拍②：write 成功终态的孪生步仍走 ``write_replay_guard_skip`` 成功面
    （既有护栏零漂移 · 本修复不得改成功孪生语义）。"""
    store = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid_a, sid_b = f"{run_id}:1", f"{run_id}:2"
    state, row_a = _mk(run_id, sid_a)
    row_b = {
        **row_a,
        "subtask_id": sid_b,
        "id": sid_b,
    }
    state["subtasks"] = [row_a, row_b]
    state["subtasks"][1]["depends_on"] = []
    done_a = {
        "subtask_id": sid_a,
        "id": sid_a,
        "type": "tool",
        "tool": _TESTING_CAP,
        "output": {"echo": "ok"},
    }
    twin_state = {**state, "subtask_results": [done_a], "inflight_subtask_ids": []}

    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        joined = await _join_subtasks(twin_state)
    skipped = next(
        (t for t in joined["subtask_results"] if str(t.get("subtask_id")) == sid_b),
        None,
    )
    assert skipped is not None, "孪生步须落终态"
    assert skipped.get("write_replay_guard_skip") is True, "成功孪生仍走 replay-guard 成功面"
    assert skipped.get("replay_of") == sid_a
    assert "output" in skipped
    assert await _live_write_tickets(store, run_id) == [], "成功孪生面不得产任何单据"
