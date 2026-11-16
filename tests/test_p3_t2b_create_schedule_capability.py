"""P3-T2b · ops.schedule.create 写类 capability 测试（issue #23 · 契约 15 §2）。

验收映射（task_p3_t2b_create_schedule_capability）：

- **manifest 校验链**：真 loader 加载 ops.schedule.v1.yaml 字段逐条钉死；
  adapter 冒号串白名单（第三前缀 app.ops.schedule.service）可解析为可调用；
  非白名单前缀 / 不存在属性 → ManifestError（loader 防线不扩容）；
- **allowlist 计数**：supervisor 候选集 9→10 含 ops.schedule.create ·
  default（MINIMAL_READONLY）不变；
- **adapter 单测（真 PG）**：直调落笔字段族（tenant/user/thread/name/
  instruction 单行化/status/fire_count/humanized_display）；422 文案逐字透传
  （interval<300 / per-user 上限 / per-tenant 上限 · 零写）；校验失败 release
  租约可安全重试；幂等重放不双写；request_id 缺省回退 run_id:subtask_id；
  缺 tenant/user 谓词 fail-closed 零写；
- **W1 HITL E2E（真 PG · 承 test_stage_w_write_expand 范式）**：
  闸拦（capability_write_hitl_required）→ pending → decide(approved) →
  resume → 重下发消费命中 → 真落笔（委派 observe 注入 user_id · 审批串链
  approval_id 三处一致）；decide(rejected) → settle 零落笔；
- **委派 off fail-closed**：delenv ENV_MODE（off）→ 批准链走通但 ctx 无
  user_id → adapter 拒（user_scope_missing）零落笔（委派是 user_id 唯一来源）。
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.idempotency import (
    InMemoryIdempotencyStore,
    reset_idempotency_store,
    set_idempotency_store,
)
from app.ops.capability.manifest import (
    MANIFEST_DIR,
    ManifestError,
    load_capability_manifest,
)
from app.ops.capability.receipts import (
    InMemoryReceiptSink,
    reset_receipt_sink,
    set_receipt_sink,
)
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import resume_hitl_run
from app.ops.hitl.store import STATUS_APPROVED, STATUS_REJECTED, InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _observe,
    _persist_hitl,
    observe_node,
    route_after_react,
    tool_exec_node,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.schedule.service import create_schedule_from_capability
from app.ops.schedule.store import (
    ERR_INTERVAL_MIN,
    ERR_KIND,
    ERR_TENANT_LIMIT,
    ERR_USER_LIMIT,
    ScheduleValidationError,
)
from app.ops.tenant_context import TENANT_A
from tests.conftest import DB_AVAILABLE

_MANIFEST = MANIFEST_DIR / "ops.schedule.v1.yaml"
_CAP = "ops.schedule.create"
_BLOCKED_BY_WRITE = "capability_write_hitl_required"

_DB_MARK = pytest.mark.skipif(not DB_AVAILABLE, reason="需要 PostgreSQL（opsdesk_test）")

# 测试数据统一前缀：清理与断言都按它过滤，绝不触碰其他行
_PREFIX = "p3t2b"


@pytest.fixture(autouse=True)
def _restore():
    dl.reset_delegation_state()
    yield
    reset_hitl_store()
    reset_idempotency_store()
    reset_receipt_sink()
    dl.reset_delegation_state()
    get_registry().clear()
    ensure_default_capabilities()


@pytest.fixture(autouse=True)
async def _db_clean():
    if DB_AVAILABLE:
        await _clear_rows()
    yield
    if DB_AVAILABLE:
        await _clear_rows()


@pytest.fixture
def schedule_env(monkeypatch):
    """新能力三层显式打开：manifest 显式加载 + schedule 写 tag 放行 + 内存幂等/回执。

    ENV_MODE 由各用例自设（observe=委派注入 user_id · delenv=off fail-closed）。
    **不设** OPS_CAPABILITY_ALLOW_WRITE——Host 单次写放行由审批命中后注入。
    """
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "schedule")
    load_capability_manifest(_MANIFEST)
    hitl_store = InMemoryHitlStore()
    set_hitl_store(hitl_store)
    set_idempotency_store(InMemoryIdempotencyStore())
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    yield hitl_store, sink


# ---------------------------------------------------------------------------
# DB 小工具（真 PostgreSQL · opsdesk_test）
# ---------------------------------------------------------------------------


async def _clear_rows() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_schedules WHERE thread_id LIKE :p"),
            {"p": f"{_PREFIX}-%"},
        )
        await session.execute(
            text("DELETE FROM ops_users WHERE username LIKE :p"),
            {"p": f"{_PREFIX}-%"},
        )


async def _mk_user():
    """建真用户（ops_schedules.user_id FK ops_users）。"""
    from app.db.models import OpsUser

    async with AsyncSessionLocal() as db:
        user = OpsUser(username=f"{_PREFIX}-{uuid.uuid4().hex[:8]}", role="viewer")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def _fetch_schedules(thread_id: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT schedule_id, tenant_id, user_id, thread_id, name, instruction,"
                " schedule_kind, status, fire_count"
                " FROM ops_schedules WHERE thread_id = :t"  # humanized_display 是 _to_dict 计算值非列
            ),
            {"t": thread_id},
        )
        cols = (
            "schedule_id", "tenant_id", "user_id", "thread_id", "name", "instruction",
            "schedule_kind", "status", "fire_count",
        )
        return [dict(zip(cols, r, strict=True)) for r in rows.all()]


async def _count_tenant_schedules(tenant_id: str) -> int:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text("SELECT schedule_id FROM ops_schedules WHERE tenant_id = :t"),
            {"t": tenant_id},
        )
        return len(rows.all())


def _write_json(tmp_path: Path, name: str, caps: list[dict]) -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps({"version": 1, "capabilities": caps}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _probe(cid: str, **over) -> dict:
    """write 探针条目（对齐 test_stage_w_write_expand 形态 · 默认合法）。"""
    cap = {
        "id": cid,
        "kind": "local_fn",
        "description": "探针",
        "when_to_use": "单测",
        "args_schema": {"type": "object", "properties": {}},
        "tags": ["probe"],
        "risk_level": "medium",
        "side_effect": "write",
        "hitl": {"required": True},
        "tenant_scoped": True,
        "idempotency_key": "{{request_id}}",
        "adapter": "local_fn:app.ops.schedule.service:create_schedule_from_capability",
    }
    cap.update(over)
    return cap


def _future_iso(hours: int = 3) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def _mk_args(thread_id: str, req_id: str | None, **over) -> dict:
    args = {
        "thread_id": thread_id,
        "name": "站会提醒",
        "instruction": "汇总\n昨日 工单",
        "schedule_kind": "once_at",
        "run_at": _future_iso(),
    }
    if req_id is not None:
        args["request_id"] = req_id
    args.update(over)
    return args


def _mk_ctx(user, tenant_id: str | None, **over) -> dict:
    ctx = {
        "tenant_id": tenant_id,
        "user_id": str(user.id),
        "run_id": "",
        "subtask_id": "",
        "approval_id": "appr-p3t2b",
    }
    ctx.update(over)
    return {k: v for k, v in ctx.items() if v is not None}


# ---------------------------------------------------------------------------
# manifest 校验链（无 DB）
# ---------------------------------------------------------------------------


def test_manifest_fields_pinned():
    """真 loader 加载 ops.schedule.v1.yaml · 字段逐条钉死（registry 真值）。"""
    result = load_capability_manifest(_MANIFEST)
    assert result.registered_ids == (_CAP,)
    entry = get_registry().get(_CAP)
    assert entry is not None
    spec, adapter = entry
    assert spec.kind == "local_fn"
    assert spec.side_effect == "write"
    assert spec.tenant_scoped is True  # V13 强制（非 mock 特例）
    assert spec.hitl_required is True  # W1：创建定时任务 = 承诺未来 LLM 花费
    assert spec.idempotency_key == "{{request_id}}"
    assert spec.risk_level == "medium"  # deny_high_risk 无豁免口
    assert "schedule" in spec.tags  # 独立写 tag（OPS_CAPABILITY_ALLOW_WRITE_TAGS=schedule）
    assert spec.enabled is True
    assert spec.reversible is True
    assert spec.execution_type == "instant"
    assert spec.max_reversal_latency == 0
    assert spec.requires_stop_support is False
    assert adapter is not None and callable(getattr(adapter, "ainvoke", None))
    # catalog 引导语逐字（用户说「每天/定时/提醒我」选中 · 一次性执行不选）
    assert spec.when_to_use == '用户要求"每天/每小时/定时/稍后自动执行"某运维查询或操作时'
    assert (
        spec.when_not_to_use
        == "一次性立即执行的请求（直接用既有 ops.* 工具）；用户未明确同意未来自动执行"
    )


def test_manifest_adapter_prefix_whitelist(tmp_path: Path):
    """adapter 冒号串白名单：第三前缀可解析；非白名单前缀 / 缺属性 → ManifestError。"""
    ok = _probe("probe.schedule.ok_prefix")
    result = load_capability_manifest(_write_json(tmp_path, "ok.json", [ok]))
    assert result.registered_ids == ("probe.schedule.ok_prefix",)

    bad_prefix = _probe(
        "probe.schedule.bad_prefix",
        adapter="local_fn:app.ops.schedule.store:create_schedule",  # store 不在白名单
    )
    with pytest.raises(ManifestError, match="非法 adapter"):
        load_capability_manifest(_write_json(tmp_path, "bad.json", [bad_prefix]))

    bad_attr = _probe(
        "probe.schedule.bad_attr",
        adapter="local_fn:app.ops.schedule.service:no_such_fn",
    )
    with pytest.raises(ManifestError, match="不可调用或不存在"):
        load_capability_manifest(_write_json(tmp_path, "badattr.json", [bad_attr]))


def test_allowlist_supervisor_9_to_10():
    """allowlist 计数：supervisor 候选集 9→10 含本能力 · default 不变。"""
    from app.ops.strategy.config import (
        CAPABILITY_ALLOWLIST_BY_KEY,
        MINIMAL_READONLY_CAPABILITY_IDS,
    )

    sup = CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]
    assert _CAP in sup
    assert len(sup) == 10
    assert CAPABILITY_ALLOWLIST_BY_KEY["default"] == list(MINIMAL_READONLY_CAPABILITY_IDS)


# ---------------------------------------------------------------------------
# adapter 单测（真 PG · 直调面）
# ---------------------------------------------------------------------------


@_DB_MARK
async def test_adapter_direct_write_fields(schedule_env):
    """直调落笔：返回字段族 + DB 行落值（tenant/user/thread/单行化/status）。"""
    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"

    out = await create_schedule_from_capability(
        _mk_args(thread_id, req_id), ctx=_mk_ctx(user, tenant)
    )
    assert out["tool"] == _CAP
    assert out["written"] is True and out["duplicated"] is False
    assert out["schedule_id"]
    assert out["status"] == "active"
    assert out["next_fire_at"]
    assert out["humanized_display"].startswith("将于 ")
    assert out["tenant_id"] == tenant
    assert out["approval_id"] == "appr-p3t2b"  # A4 审批串链
    assert out["idempotency_key"] == req_id

    rows = await _fetch_schedules(thread_id)
    assert len(rows) == 1
    row = rows[0]
    assert str(row["schedule_id"]) == out["schedule_id"]
    assert row["tenant_id"] == tenant
    assert str(row["user_id"]) == str(user.id)
    assert row["name"] == "站会提醒"
    assert row["instruction"] == "汇总 昨日 工单"  # 单行化（store 语义）
    assert row["status"] == "active" and row["fire_count"] == 0


@_DB_MARK
async def test_adapter_422_interval_passthrough(schedule_env):
    """422 透传①：interval<300 → §1.8 逐字文案原样上抛（不改写）· 零写。"""
    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    with pytest.raises(ScheduleValidationError) as excinfo:
        await create_schedule_from_capability(
            _mk_args(
                thread_id, req_id,
                schedule_kind="interval", run_at=None, interval_seconds=120,
            ),
            ctx=_mk_ctx(user, tenant),
        )
    assert str(excinfo.value) == ERR_INTERVAL_MIN
    assert await _fetch_schedules(thread_id) == []


@_DB_MARK
async def test_adapter_422_kind_vocabulary_passthrough(schedule_env):
    """422 透传③：词表外 schedule_kind → 逐字文案原样上抛（不改写）· 零写。"""
    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    with pytest.raises(ScheduleValidationError) as excinfo:
        await create_schedule_from_capability(
            _mk_args(thread_id, req_id, schedule_kind="hourly"),
            ctx=_mk_ctx(user, tenant),
        )
    assert str(excinfo.value) == ERR_KIND
    assert await _fetch_schedules(thread_id) == []


@_DB_MARK
async def test_adapter_422_dual_quota_passthrough(schedule_env, monkeypatch):
    """422 透传②：双上限（per-user 20 / per-tenant 200）逐字文案原样上抛 · 零写。

    测试内 patch 常量缩小上限（文案常量本身含 20/200 字样 · 逐字断言不受影响）。
    """
    from app.ops.schedule import store as schedule_store

    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"

    # per-user 上限：patch 为 2 → 第三条触发 ERR_USER_LIMIT
    monkeypatch.setattr(schedule_store, "MAX_ACTIVE_PER_USER", 2)
    for i in range(2):
        out = await create_schedule_from_capability(
            _mk_args(f"{_PREFIX}-th-u{i}-{uuid.uuid4().hex[:6]}",
                     f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"),
            ctx=_mk_ctx(user, tenant),
        )
        assert out["written"] is True
    with pytest.raises(ScheduleValidationError) as excinfo:
        await create_schedule_from_capability(
            _mk_args(f"{_PREFIX}-th-u9-{uuid.uuid4().hex[:6]}",
                     f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"),
            ctx=_mk_ctx(user, tenant),
        )
    assert str(excinfo.value) == ERR_USER_LIMIT
    assert await _count_tenant_schedules(tenant) == 2

    # per-tenant 上限：新用户（绕开 per-user）· patch 租户上限为当前存量 2 →
    # 第三条（租户口径）触发 ERR_TENANT_LIMIT
    monkeypatch.setattr(schedule_store, "MAX_ACTIVE_PER_USER", 20)
    monkeypatch.setattr(schedule_store, "MAX_PER_TENANT", 2)
    user2 = await _mk_user()
    with pytest.raises(ScheduleValidationError) as excinfo2:
        await create_schedule_from_capability(
            _mk_args(f"{_PREFIX}-th-t9-{uuid.uuid4().hex[:6]}",
                     f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"),
            ctx=_mk_ctx(user2, tenant),
        )
    assert str(excinfo2.value) == ERR_TENANT_LIMIT
    assert await _count_tenant_schedules(tenant) == 2


@_DB_MARK
async def test_adapter_validation_failure_releases_lease(schedule_env):
    """校验失败 = 无副作用 → release 租约：同幂等键修正参数后可安全重试。"""
    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    ctx = _mk_ctx(user, tenant)
    with pytest.raises(ScheduleValidationError):
        await create_schedule_from_capability(
            _mk_args(thread_id, req_id, schedule_kind="interval",
                     run_at=None, interval_seconds=120),
            ctx=ctx,
        )
    # 同键重试（修正 interval）→ 正常落笔（不判 in_flight / duplicate）
    out = await create_schedule_from_capability(
        _mk_args(thread_id, req_id, schedule_kind="interval",
                 run_at=None, interval_seconds=600),
        ctx=ctx,
    )
    assert out["written"] is True
    assert len(await _fetch_schedules(thread_id)) == 1


@_DB_MARK
async def test_adapter_idempotent_replay_no_double_write(schedule_env):
    """幂等重放：同 request_id 第二次直返 duplicate 对账载荷 · 不双写。"""
    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    ctx = _mk_ctx(user, tenant)
    args = _mk_args(thread_id, req_id)

    first = await create_schedule_from_capability(args, ctx=ctx)
    assert first["written"] is True
    replay = await create_schedule_from_capability(args, ctx=ctx)
    assert replay["duplicated"] is True and replay["written"] is False
    assert replay["idempotency_key"] == req_id
    assert len(await _fetch_schedules(thread_id)) == 1


@_DB_MARK
async def test_adapter_request_id_fallback_run_subtask(schedule_env):
    """偏差 D3：request_id 缺省回退 {run_id}:{subtask_id}；同 subtask 重放不双写。"""
    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    ctx = _mk_ctx(user, tenant, run_id=f"{_PREFIX}-run-1", subtask_id=f"{_PREFIX}-run-1:1")
    args = _mk_args(thread_id, None)  # 无 request_id

    out = await create_schedule_from_capability(args, ctx=ctx)
    assert out["written"] is True
    assert out["idempotency_key"] == f"{_PREFIX}-run-1:{_PREFIX}-run-1:1"
    replay = await create_schedule_from_capability(args, ctx=ctx)
    assert replay["duplicated"] is True
    assert len(await _fetch_schedules(thread_id)) == 1

    # 两者皆无 → 不落笔
    with pytest.raises(ValueError, match="幂等键缺失不落笔"):
        await create_schedule_from_capability(args, ctx=_mk_ctx(user, tenant))


@_DB_MARK
async def test_adapter_missing_predicates_failclosed(schedule_env):
    """归属谓词 fail-closed：缺 tenant → tenant_scope_missing；缺 user →
    user_scope_missing（委派 off 直调面同源）· 均零写。"""
    user = await _mk_user()
    tenant = f"{_PREFIX}-t-{uuid.uuid4().hex[:8]}"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    with pytest.raises(PermissionError, match="tenant_scope_missing"):
        await create_schedule_from_capability(
            _mk_args(thread_id, req_id), ctx=_mk_ctx(user, None)
        )
    with pytest.raises(PermissionError, match="user_scope_missing"):
        await create_schedule_from_capability(
            _mk_args(thread_id, req_id), ctx={"tenant_id": tenant}
        )
    assert await _fetch_schedules(thread_id) == []


# ---------------------------------------------------------------------------
# W1 HITL E2E（真 PG · 承 test_stage_w_write_expand A1/A2 范式）
# ---------------------------------------------------------------------------


def _mk_state(run_id: str, sid: str, user, thread_id: str, req_id: str) -> tuple[dict, dict]:
    """单步写 tool 计划 state + 该步 row（user_id 入 state · 委派链注入 ctx）。"""
    args = _mk_args(thread_id, req_id)
    state = {
        "messages": [HumanMessage(content="三小时后提醒我站会")],
        "run_id": run_id,
        "user_id": str(user.id),
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": dict(args),
                "args": dict(args),
                "tool": _CAP,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [],
        "allowed_capability_ids": [_CAP],
    }
    return state, state["subtasks"][0]


def _observe_graph_factory(*, checkpointer):
    """只含真 observe_node 的最小图（承 stage_w / test_hitl_resume harness）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=checkpointer)


async def _drive_to_suspended(state, row, *, graph_thread: str):
    """闸拦 → pending → 图真挂起，返回 (merged, req, saver)。"""
    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE
    assert blocked.get("hitl_required") is True
    assert blocked.get("tenant_id") == TENANT_A

    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [row["subtask_id"]]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id=graph_thread)
    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == row["subtask_id"])
    assert req["blocked_by"] == _BLOCKED_BY_WRITE
    assert req["tenant_id"] == TENANT_A
    intent = req["payload"]["write_intent"]
    assert intent["capability_id"] == _CAP
    assert intent["tenant_id"] == TENANT_A

    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": graph_thread}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None and suspended["reason"] == "hitl_waiting"
    return merged, req, saver


@_DB_MARK
async def test_hitl_approve_resume_real_write(schedule_env, monkeypatch):
    """E2E 通过：委派 observe 注入 user_id → 批准 → resume → 重下发 → 真落笔。

    串链断言：拦单/审批行/执行行 tenant 一致 · approval_id 入输出与回执。
    """
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    hitl, sink = schedule_env
    user = await _mk_user()
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    req_id = f"{run_id}-req"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    state, row = _mk_state(run_id, sid, user, thread_id, req_id)

    merged, req, saver = await _drive_to_suspended(state, row, graph_thread="t-p3t2b-a")
    assert await _fetch_schedules(thread_id) == []  # 批准前零落笔

    decided = await hitl.adecide(req["id"], decision=STATUS_APPROVED, by="验收")
    assert decided["status"] == STATUS_APPROVED
    resumed = await resume_hitl_run(
        thread_id="t-p3t2b-a",
        approved=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    final = resumed["state"]
    assert final["react_observation"]["verdict"] == "replan"
    assert final["hitl_unlocked_ids"] == [sid]

    post = {**merged, "hitl_unlocked_ids": final["hitl_unlocked_ids"]}
    exec_out = await tool_exec_node({**post, "assigned_subtask": row})
    result = exec_out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    assert "error" not in result, f"批准后重下发仍失败：{result.get('error')!r}"
    output = result["output"]
    assert output["written"] is True
    assert output["tool"] == _CAP
    assert output["approval_id"] == req["id"]  # A4：输出串审批单

    rows = await _fetch_schedules(thread_id)
    assert len(rows) == 1
    db_row = rows[0]
    assert str(db_row["schedule_id"]) == output["schedule_id"]
    assert db_row["tenant_id"] == TENANT_A  # A3：执行行租户=拦单/审批行租户
    assert str(db_row["user_id"]) == str(user.id)  # 归属=调用者（委派注入 · 非模型产出）
    assert db_row["name"] == "站会提醒"
    assert db_row["status"] == "active"

    receipts = sink.by_idempotency_key(req_id)
    assert len(receipts) == 1
    assert receipts[0].ok is True
    assert receipts[0].write_confirmed is True  # Host 单次放行下执行
    assert receipts[0].tenant_id == TENANT_A
    assert receipts[0].captured.get("schedule_id") == output["schedule_id"]


@_DB_MARK
async def test_hitl_rejected_settles_without_write(schedule_env, monkeypatch):
    """E2E 拒绝：decide(rejected) → resume 收工（settle）· 不执行 · 零落笔。"""
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    hitl, _sink = schedule_env
    user = await _mk_user()
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    state, row = _mk_state(run_id, sid, user, thread_id, f"{run_id}-req")

    _merged, req, saver = await _drive_to_suspended(state, row, graph_thread="t-p3t2b-r")
    await hitl.adecide(req["id"], decision=STATUS_REJECTED, by="验收")
    resumed = await resume_hitl_run(
        thread_id="t-p3t2b-r",
        approved=[],
        rejected=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    assert resumed["state"]["react_observation"]["verdict"] == "settle"
    assert await _fetch_schedules(thread_id) == []


@_DB_MARK
async def test_delegation_off_failclosed_no_user_id(schedule_env, monkeypatch):
    """委派 off（delenv）：批准链走通但 ctx 无 user_id（委派是 user_id 唯一来源）
    → adapter fail-closed（user_scope_missing）· 零落笔。"""
    monkeypatch.delenv(dl.ENV_MODE, raising=False)  # off：ctx 不注入 user_id
    hitl, _sink = schedule_env
    user = await _mk_user()
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    thread_id = f"{_PREFIX}-th-{uuid.uuid4().hex[:8]}"
    state, row = _mk_state(run_id, sid, user, thread_id, f"{run_id}-req")

    merged, req, saver = await _drive_to_suspended(state, row, graph_thread="t-p3t2b-o")
    await hitl.adecide(req["id"], decision=STATUS_APPROVED, by="验收")
    resumed = await resume_hitl_run(
        thread_id="t-p3t2b-o",
        approved=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    post = {**merged, "hitl_unlocked_ids": resumed["state"]["hitl_unlocked_ids"]}
    exec_out = await tool_exec_node({**post, "assigned_subtask": row})
    result = exec_out["subtask_results"][-1]
    assert "user_scope_missing" in str(result.get("error") or "")
    assert await _fetch_schedules(thread_id) == []
