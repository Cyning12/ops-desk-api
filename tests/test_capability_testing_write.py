"""testing-write-capability（D2）：测试专用写能力 manifest + 裁定四 loader 放宽 + env 门控放行。

覆盖（task_testing_write_capability 验收映射）：

- **A8 ①–④** loader 校验（裁定四）：write+local_fn 两键皆缺仍 ManifestError
 （V1 不放松 · 文案逐字节钉死 baseline_v1.json:134）/ 顶层 idempotency_key
  可加载 / read 无顶层键加载零 diff / read 误声明顶层键 → V8 拦
 （文案钉死 baseline_v1.json:102）；
- **A6** 字段钉死（加载后经 registry 断言七字段）+ **A4②** adapter 可调（罐头 dict）；
- **A4③ / A5** 罐头 adapter 零 IO 防线（inspect 函数体无 IO 调用 · docstring 含
  「语义 mock」）；
- **A4①** `allow_write_tags_any` 三例：命中→豁免 deny_write 一层 /
  未命中→仍裁 / high risk 即使命中仍裁（deny_high_risk 永不豁免）；
- **A3** 加载≠可见：只加载不放行 → registry 含条目 · baseline 可见集不含；
- 放行口径自检（failure_paths 预案）：`OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing`
  后 baseline 可见集**必含**该条目（不达标则验收链不可达）；
- **A2** off 零 diff：三 env 皆不设 → 注册表 snapshot 不含 · 可见集与基线一致
 （builtin 5 枚；加载 oa 清单后 8 枚）· catalog count 不变；
- **A4④** enforce 集成（真 loader 条目 + 真 `_join_subtasks`/`_observe`/
  `_persist_hitl`/`observe_node`/`resume_hitl_run`）：挂起（blocked_by=
  delegation_issue_hitl_required）→ pending 可见 → decide(approved) →
  resume（图真恢复 · verdict=replan · 解锁留痕）。
  **设计真态**（hitl-approval-consumption-loop T1 落地后）：批准后重下发同 tool
  经消费门放行（匹配 approved 单据 → 签发判定 None）；无消费形态仍拦——
  双断言钉死于 A4④ 末段，边界否定全组由 tests/test_hitl_approval_consumption.py
  TA2 承接。live HTTP 全链证据留 40 复跑。
"""

from __future__ import annotations

import inspect
import json
import uuid
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.ops.capability import delegation as dl
from app.ops.capability import invoke, list_capabilities
from app.ops.capability.baseline import (
    ENV_ALLOW_WRITE_TAGS,
    baseline_filter,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.defaults import (
    testing_write_echo as _testing_write_echo,  # 别名：避免 pytest 按 test* 误收集
)
from app.ops.capability.gateway import get_registry
from app.ops.capability.manifest import (
    MANIFEST_DIR,
    ManifestError,
    extra_manifest_paths,
    load_capability_manifest,
)
from app.ops.capability.registry import _match_filter
from app.ops.capability.types import CapabilityFilter, CapabilitySpec
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import resume_hitl_run
from app.ops.hitl.store import STATUS_APPROVED, InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _delegation_issue_block_reason,
    _join_subtasks,
    _observe,
    _persist_hitl,
    observe_node,
    route_after_react,
)
from app.ops.lg_rag.state import LgRagState

_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"
_OA_MANIFEST = MANIFEST_DIR / "oa.readonly.v1.yaml"
_TESTING_CAP = "testing.write.echo"

_BUILTIN_IDS = {
    "mock_get_issue_status",
    "mock_get_deploy_info",
    "utc_now_iso",
    "get_issue_by_number",
    "get_pr_by_number",
}
_OA_IDS = {"oa.doc.search", "oa.org.whois", "oa.todo.mine"}

# write+local_fn 探针条目的公共字段（A8 用 · 对齐 test_capability_manifest_http 形态）
_PROBE_BASE = {
    "id": "probe.cap",
    "kind": "local_fn",
    "description": "探针",
    "when_to_use": "单测",
    "args_schema": {"type": "object", "properties": {}},
    "adapter": "local_fn:app.ops.capability.defaults:utc_now_iso",
}


@pytest.fixture(autouse=True)
def _restore():
    dl.reset_delegation_state()
    yield
    reset_hitl_store()
    dl.reset_delegation_state()
    get_registry().clear()
    ensure_default_capabilities()


def _write_json(tmp_path: Path, name: str, caps: list[dict]) -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps({"version": 1, "capabilities": caps}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# A8 · loader 校验（裁定四：V1 二选一放宽 · V8 对称适配 · 文案逐字节不变）
# ---------------------------------------------------------------------------


def test_a8_v1_still_blocks_write_local_fn_without_any_key(tmp_path: Path):
    """① write+local_fn 且 http 块键与顶层键皆缺 → 仍 ManifestError（V1 不放松）。

    错误文案逐字节钉死（golden baseline_v1.json:134 对拍面 · O5）。
    """
    cap = dict(
        _PROBE_BASE,
        id="probe.write_nokey",
        side_effect="write",
        hitl={"required": True},
    )
    with pytest.raises(ManifestError, match="V1: side_effect=write 必须有 idempotency_key"):
        load_capability_manifest(_write_json(tmp_path, "v1.json", [cap]))
    assert "probe.write_nokey" not in {s.capability_id for s in list_capabilities()}


def test_a8_write_local_fn_with_top_level_key_loads(tmp_path: Path):
    """② write+local_fn + 顶层 idempotency_key → 可加载（裁定四放宽的唯一新出口）。

    V13 补注（stage-w-write-expand · SPEC v0.1 Q4）：写能力 tenant_scoped 强制
    （mock 特例清单不扩容）——本 probe 补 ``tenant_scoped: true`` 以过新断言；
    断言对象（V1 放宽面）不变。
    """
    cap = dict(
        _PROBE_BASE,
        id="probe.write_topkey",
        side_effect="write",
        tenant_scoped=True,
        hitl={"required": True},
        idempotency_key="{{request_id}}",
    )
    result = load_capability_manifest(_write_json(tmp_path, "ok.json", [cap]))
    assert "probe.write_topkey" in result.registered_ids
    spec = next(s for s in list_capabilities() if s.capability_id == "probe.write_topkey")
    assert spec.idempotency_key == "{{request_id}}"
    assert spec.hitl_required is True  # V2 语义不动


def test_a8_read_without_top_level_key_zero_diff(tmp_path: Path):
    """③ read 条目（无顶层键）加载路径与基线零 diff：照常注册且新字段缺省 None。"""
    cap = dict(_PROBE_BASE, id="probe.read_plain", side_effect="read")
    result = load_capability_manifest(_write_json(tmp_path, "read.json", [cap]))
    assert "probe.read_plain" in result.registered_ids
    spec = next(s for s in list_capabilities() if s.capability_id == "probe.read_plain")
    assert spec.idempotency_key is None


def test_a8_read_with_top_level_key_hits_v8(tmp_path: Path):
    """④ read 误声明顶层 idempotency_key → ManifestError（V8 对称适配）。

    错误文案逐字节钉死（golden baseline_v1.json:102 对拍面 · O5）。
    """
    cap = dict(_PROBE_BASE, id="probe.read_key", side_effect="read", idempotency_key="x")
    with pytest.raises(ManifestError, match="V8: side_effect=read 不应声明 idempotency_key"):
        load_capability_manifest(_write_json(tmp_path, "v8.json", [cap]))
    assert "probe.read_key" not in {s.capability_id for s in list_capabilities()}


# ---------------------------------------------------------------------------
# F1/F2 + A6 + A4② · testing.v1.yaml 显式加载与字段钉死
# ---------------------------------------------------------------------------


def test_a6_manifest_loads_and_fields_pinned():
    """A6：经真 loader 加载 testing.v1.yaml，字段钉死逐条断言（registry 真值）。"""
    result = load_capability_manifest(_TESTING_MANIFEST)
    assert result.registered_ids == (_TESTING_CAP,)
    entry = get_registry().get(_TESTING_CAP)
    assert entry is not None
    spec, adapter = entry
    assert spec.side_effect == "write"  # 触发 issuance_policy_allows 条件②不放行
    assert spec.kind == "local_fn"
    assert spec.hitl_required is True  # V2 强制 · 与本 capability 用途自洽
    assert spec.idempotency_key  # 顶层幂等键非空（裁定四声明位）
    assert spec.risk_level != "high"  # deny_high_risk 无豁免口 · 标 high 永不可见
    assert "testing" in spec.tags
    assert spec.enabled is True
    assert spec.tenant_scoped is False
    # 可撤销性四字段齐（字段族对齐 builtin 范式）
    assert spec.reversible is True
    assert spec.execution_type == "instant"
    assert spec.max_reversal_latency == 0
    assert spec.requires_stop_support is False
    # A4②：adapter 可调且返回罐头 dict（语义 mock）
    out = adapter.invoke({"request_id": "r-1", "note": "demo"})
    assert out["tool"] == "testing_write_echo"
    assert out["written"] is False
    # 统一 invoke 面：Policy 写闸仍在第二道把守（hitl_required 未确认即拦）——
    # 放行口径只动可见集裁剪，不动 Policy（钉死契约 · 两道闸都要有）
    result2 = invoke(_TESTING_CAP, {"request_id": "r-2"})
    assert result2.ok is False
    assert (result2.error or "").startswith("policy_blocked")


# ---------------------------------------------------------------------------
# A4③ / A5 · 罐头 adapter 零 IO 防线
# ---------------------------------------------------------------------------


def test_a5_canned_adapter_zero_io():
    """A5 防线机械化：函数体（AST · 剔除 docstring）无 IO 调用/无 import；
    docstring 含「语义 mock」。"""
    import ast

    src = inspect.getsource(_testing_write_echo)
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    body = [
        n
        for n in fn.body
        if not (
            isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        )  # 剔除 docstring（其内合法提及「零 subprocess」等纪律词）
    ]
    body_src = ast.unparse(ast.Module(body=body, type_ignores=[]))
    for token in (
        "requests",
        "httpx",
        "subprocess",
        "open(",
        ".write",
        "Path",
        "socket",
        "urlopen",
    ):
        assert token not in body_src, f"罐头函数体出现禁用形态: {token}"
    # 函数体不得 import 任何库（IO 库禁令的机械闸）
    assert not [
        n
        for n in ast.walk(ast.Module(body=body, type_ignores=[]))
        if isinstance(n, ast.Import | ast.ImportFrom)
    ]
    assert _testing_write_echo.__doc__ is not None
    assert "语义 mock" in _testing_write_echo.__doc__
    # 纯函数罐头 dict：两次调用同参同果 · 无状态
    assert _testing_write_echo({"note": "x"}) == _testing_write_echo({"note": "x"})


# ---------------------------------------------------------------------------
# F3 + A4① · allow_write_tags_any 放行口径（只豁免 deny_write 一层）
# ---------------------------------------------------------------------------


def _write_spec(cid: str, **over) -> CapabilitySpec:
    base = {
        "capability_id": cid,
        "kind": "local_fn",
        "description": "单测",
        "args_schema": {"type": "object", "properties": {}},
        "tags": ("testing",),
        "side_effect": "write",
        "risk_level": "medium",
        "when_to_use": "单测",
    }
    base.update(over)
    return CapabilitySpec(**base)


def test_allow_write_tags_hit_exempts_deny_write_only():
    """命中 → 豁免 deny_write 一层（可见）。"""
    spec = _write_spec("x.write")
    flt = CapabilityFilter(deny_write=True, allow_write_tags_any=frozenset({"testing"}))
    assert _match_filter(spec, flt) is True


def test_allow_write_tags_miss_still_cropped():
    """未命中 → deny_write 仍裁（默认空=None 时判序零 diff 一并守住）。"""
    spec = _write_spec("x.write")
    miss = CapabilityFilter(deny_write=True, allow_write_tags_any=frozenset({"other"}))
    assert _match_filter(spec, miss) is False
    # 默认 None（env 未设）→ 与旧判序逐字节一致
    default = CapabilityFilter(deny_write=True)
    assert _match_filter(spec, default) is False


def test_allow_write_tags_never_exempts_deny_high_risk():
    """high risk 即使命中 tag 仍裁：deny_high_risk 判序在前且**永不豁免**。"""
    spec = _write_spec("x.write_high", risk_level="high")
    flt = CapabilityFilter(
        deny_high_risk=True,
        deny_write=True,
        allow_write_tags_any=frozenset({"testing"}),
    )
    assert _match_filter(spec, flt) is False


def test_baseline_env_default_empty_is_none(monkeypatch):
    """env 默认空 → 字段 None（判序零 diff）；设置后逗号分隔解析生效。"""
    monkeypatch.delenv(ENV_ALLOW_WRITE_TAGS, raising=False)
    assert baseline_filter(node_role="probe").allow_write_tags_any is None
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing, mock")
    assert baseline_filter(node_role="probe").allow_write_tags_any == frozenset({"testing", "mock"})


# ---------------------------------------------------------------------------
# A2 / A3 · off 零 diff 与 加载≠可见
# ---------------------------------------------------------------------------


def test_a2_off_zero_diff(monkeypatch):
    """三 env 皆不设：注册表/可见集/catalog 计数与 master 基线一致。"""
    monkeypatch.delenv("OPS_CAPABILITY_EXTRA_MANIFESTS", raising=False)
    monkeypatch.delenv(ENV_ALLOW_WRITE_TAGS, raising=False)
    monkeypatch.delenv("LG_RAG_DELEGATION_TOKEN_MODE", raising=False)
    # 默认加载面不含 testing.v1.yaml（显式文件列表纪律 · 非目录扫描）
    assert extra_manifest_paths() == ()
    snap = get_registry().snapshot()
    assert _TESTING_CAP not in snap["capability_ids"]
    assert snap["count"] == 5  # builtin 五枚 · catalog count 不变
    # 可见集：默认 builtin 5 枚；加载 oa 清单后恰 8 枚（验收基线口径）· 均不含本条目
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert ids == _BUILTIN_IDS
    load_capability_manifest(_OA_MANIFEST)
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert ids == _BUILTIN_IDS | _OA_IDS
    assert _TESTING_CAP not in ids


def test_a3_loaded_but_not_visible_without_allow_env(monkeypatch):
    """A3：加载≠可见——只 EXTRA_MANIFESTS（此处直接 load）不设 ALLOW_WRITE_TAGS，
    注册表含条目但 baseline 可见集不含（deny_write 不全局松）。"""
    monkeypatch.delenv(ENV_ALLOW_WRITE_TAGS, raising=False)
    load_capability_manifest(_TESTING_MANIFEST)
    snap = get_registry().snapshot()
    assert _TESTING_CAP in snap["capability_ids"]
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _TESTING_CAP not in ids


def test_allow_write_env_makes_testing_cap_visible(monkeypatch):
    """放行口径自检（failure_paths 预案）：双 env 齐设 → baseline 可见集必含该条目，
    否则 enforce 验收链不可达（tool ∉ scope 不走 HITL）。
    env 读取在 baseline_filter 调用时生效（重建 filter · 不依赖 import 顺序）。
    """
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    load_capability_manifest(_TESTING_MANIFEST)
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _TESTING_CAP in ids
    # 既有只读面不受影响
    assert ids >= _BUILTIN_IDS


# ---------------------------------------------------------------------------
# A4④ · enforce 集成：挂起 → pending → decide(approved) → resume（真节点链）
# ---------------------------------------------------------------------------


def _observe_graph_factory(*, checkpointer):
    """只含真 observe_node 的最小图（承 test_hitl_resume harness · interrupt 需真实 runnable）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=checkpointer)


@pytest.mark.asyncio
async def test_a4_enforce_chain_suspend_pending_decide_resume(monkeypatch):
    """enforce + 放行 env 下，真实加载条目走真判定链的全链机制断言。

    挂起（真 _join_subtasks → delegation_issue_hitl_required）→ pending 落库可见
    （真 _persist_hitl）→ decide(approved)（真 store.adecide）→ resume
    （真 resume_hitl_run + 真 observe_node · verdict=replan · 解锁留痕）。

    **D1/D2 落地后设计真态**（hitl-approval-consumption-loop T1）：批准后重下发
    同 tool 经消费门放行（匹配 approved 单据 · 三元组+TTL）；单步无前缀计划
    unlock_subtask_id 回填为被拦 sid 自身（delegation_issue 类形态守卫），
    HTTP resume 端点对该形态不再 409。live HTTP 全链证据留 40 复跑。
    """
    monkeypatch.setenv(dl.ENV_MODE, "enforce")
    monkeypatch.setenv(dl.ENV_SECRET, "testing-write-secret")
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    load_capability_manifest(_TESTING_MANIFEST)
    # 放行自检：可见集必含该条目，否则全链不可达（failure_paths 预案）
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _TESTING_CAP in ids

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state = {
        "messages": [HumanMessage(content="演示写操作审批")],
        "run_id": run_id,
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": {"request_id": "r-1", "note": "demo"},
                "tool": _TESTING_CAP,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [sid],
        "allowed_capability_ids": [_TESTING_CAP],
    }

    # ① 挂起：真判定链（issuance_policy_allows 条件②不放行 → 委派签发需人工审批）
    joined = await _join_subtasks({**state, "inflight_subtask_ids": []})
    assert sid not in joined.get("inflight_subtask_ids", [])
    blocked = [r for r in joined["subtask_results"] if r.get("hitl_required") is True]
    assert len(blocked) == 1
    assert blocked[0]["blocked_by"] == "delegation_issue_hitl_required"

    store = InMemoryHitlStore()
    set_hitl_store(store)
    merged = {
        **state,
        "subtask_results": list(joined.get("subtask_results") or []),
        "inflight_subtask_ids": [],
    }
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-a4")
    assert unpersisted is False

    # ② pending 可见（挂起载荷 requests 与 store 行双口径）
    rows = await store.alist(status="pending", limit=10)
    req = next(r for r in rows if str(r.get("subtask_id") or "") == sid)
    assert req["blocked_by"] == "delegation_issue_hitl_required"

    # 图真挂起：interrupt 载荷 reason=hitl_waiting 且带本申请
    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-a4"}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None, "前置：图没有被挂起"
    assert suspended["reason"] == "hitl_waiting"
    assert any(r["blocked_by"] == "delegation_issue_hitl_required" for r in suspended["requests"])

    # ③ decide(approved)：真 store 守卫（pending → approved）
    decided = await store.adecide(req["id"], decision=STATUS_APPROVED, by="验收")
    assert decided["status"] == STATUS_APPROVED

    # ④ resume：真驱动器把批准喂回挂起点 → 图真恢复（解锁留痕 · verdict=replan）
    out = await resume_hitl_run(
        thread_id="t-a4",
        approved=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    final = out["state"]
    assert final["react_observation"]["verdict"] == "replan"
    assert final["hitl_unlocked_ids"] == [sid]
    assert final["react_observation"]["hitl_decision"]["decided_by"] == "验收"

    # 设计真态钉死（D1 消费门落地后语义 · 双断言 · 边界否定由 TA2 全组承接）：
    # ① 有消费形态（匹配 approved 单据 · 三元组命中 · decided_at 新鲜）→
    #   重下发同 tool 放行签发（None）——批准接成可消费的授权；
    # ② 无消费形态（消费键不命中：换 run_id）→ issuance_policy_allows 仍判非只读 →
    #   再拦（无匹配单据时审批逐次有效语义不变）。
    post = dict(merged)
    post["hitl_unlocked_ids"] = final["hitl_unlocked_ids"]
    reason = await _delegation_issue_block_reason(post, merged["subtasks"][0])
    assert reason is None
    post_mismatch = {**post, "run_id": f"{run_id}-other"}
    reason_mismatch = await _delegation_issue_block_reason(post_mismatch, merged["subtasks"][0])
    assert reason_mismatch is not None and "非只读" in reason_mismatch
