"""P3-T4 · runs 只读端点测试（真 PG · 契约 15-p3-contracts.md §3）。

覆盖 task 验收可机断项：
- §3.1 runs 列表：投影字段族 / status 六词表原值 / query_summary 截 80 /
  schedule_attribution（临时建表路径 + 表缺位降级 null）
- keyset 分页（created_at desc, run_id）：默认 20 · 上限 50（超限 422）·
  跨页不重不漏 · 坏 cursor 422
- §3.2 events：白名单 8 值 SQL 层过滤（词表外行不落响应）· 500 帧截断 +
  next_after_seq 续拉 · 事件对象仅四字段
- 404 矩阵：跨用户/未知 thread 与 run → 404（不 403）· 未登录 → 401
- 空形态：thread 零 runs → 200 空列表；run 零帧 → 404（assert_run_owned
  既有语义）；run 仅词表外帧 → 200 空 events

DB 用例造 ops_lg_rag_threads / ops_lg_rag_runs / ops_lg_rag_run_events 行；
schedule 归因路径以 raw SQL 临时建 ops_schedules/ops_schedule_fires（契约钉名
最小列集 · 测后 drop · 不碰 alembic · R-P3-T4-1）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, text

from app.db.models import OpsLgRagRun, OpsLgRagRunEvent, OpsLgRagThread, OpsUser
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE

_DB_SKIP = pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")

_RUNS = "/api/ops/lg-rag/threads/{tid}/runs"
_EVENTS = "/api/ops/lg-rag/runs/{rid}/events"

# conftest override_auth_maintainer / override_auth_viewer 固定 id
MAINTAINER_ID = "00000000-0000-0000-0000-000000000001"
VIEWER_ID = "00000000-0000-0000-0000-000000000002"

_BASE_TS = datetime(2026, 10, 1, 8, 0, 0)

# §0 冻结词表 8 值（白名单全集 · 对拍锚）
_ALLOWED_8 = [
    "run.start",
    "answer",
    "subtask.progress",
    "node.progress",
    "hitl.waiting",
    "done",
    "error",
    "hitl.resumed",
]


def _ev(
    run_id: str,
    seq: int,
    user_id: str,
    thread_id: str,
    event_type: str,
    payload: dict[str, Any],
    created_at: datetime,
    *,
    role: str = "system",
) -> OpsLgRagRunEvent:
    return OpsLgRagRunEvent(
        run_id=run_id,
        seq=seq,
        user_id=user_id,
        thread_id=thread_id,
        ts_ms=int((created_at - _BASE_TS).total_seconds() * 1000),
        agent_role=role,
        event_type=event_type,
        payload=payload,
        created_at=created_at,
    )


def _run(
    run_id: str,
    user_id: str,
    thread_id: str,
    status: str,
    created_at: datetime,
    *,
    finished_at: datetime | None = None,
) -> OpsLgRagRun:
    return OpsLgRagRun(
        run_id=run_id,
        tenant_id="",
        user_id=user_id,
        thread_id=thread_id,
        status=status,
        created_at=created_at,
        finished_at=finished_at,
    )


@pytest.fixture
async def seed():
    """造行工厂；按前缀清场（只删本测试造的前缀与用户）。

    events/runs/threads 均有 FK → ops_users：先补用户行再落业务行。
    """
    prefix = f"p3t4-{uuid.uuid4().hex[:8]}"
    created_users: list[str] = []

    async with AsyncSessionLocal() as db:
        for uid in (MAINTAINER_ID, VIEWER_ID):
            if await db.get(OpsUser, uid) is None:
                db.add(OpsUser(id=uid, username=f"{prefix}-{uid[-4:]}", role="viewer"))
                created_users.append(uid)
        await db.commit()

    async def _add(*rows: Any) -> None:
        async with AsyncSessionLocal() as db:
            db.add_all(rows)
            await db.commit()

    yield prefix, _add

    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(OpsLgRagRunEvent).where(OpsLgRagRunEvent.thread_id.like(f"{prefix}%"))
        )
        await db.execute(delete(OpsLgRagRun).where(OpsLgRagRun.thread_id.like(f"{prefix}%")))
        await db.execute(delete(OpsLgRagThread).where(OpsLgRagThread.id.like(f"{prefix}%")))
        for uid in created_users:
            await db.execute(delete(OpsUser).where(OpsUser.id == uid))
        await db.commit()


# ---------------------------------------------------------------------------
# §3.1 runs 列表
# ---------------------------------------------------------------------------


@_DB_SKIP
async def test_runs_list_happy_projection(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    prefix, add = seed
    tid = f"{prefix}-th"
    rid1, rid2, rid3 = (f"{prefix}-r{i}" for i in (1, 2, 3))
    long_query = "  " + "字" * 100 + "  "
    await add(OpsLgRagThread(id=tid, user_id=MAINTAINER_ID))
    await add(
        _run(rid1, MAINTAINER_ID, tid, "running", _BASE_TS),
        _run(rid2, MAINTAINER_ID, tid, "waiting_approval", _BASE_TS + timedelta(minutes=1)),
        _run(
            rid3,
            MAINTAINER_ID,
            tid,
            "done",
            _BASE_TS + timedelta(minutes=2),
            finished_at=_BASE_TS + timedelta(minutes=3),
        ),
    )
    await add(
        _ev(rid1, 1, MAINTAINER_ID, tid, "run.start", {"query": "查一下工单"}, _BASE_TS),
        _ev(rid2, 1, MAINTAINER_ID, tid, "run.start", {"query": long_query}, _BASE_TS),
        # rid3 无 run.start 帧 → query_summary None
        _ev(rid3, 1, MAINTAINER_ID, tid, "done", {"status": "done"}, _BASE_TS + timedelta(minutes=3)),
    )
    resp = await client.get(_RUNS.format(tid=tid))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    runs = body["data"]["runs"]
    assert body["data"]["next_cursor"] is None
    assert [r["run_id"] for r in runs] == [rid3, rid2, rid1]  # created_at desc
    assert set(runs[0].keys()) == {
        "run_id",
        "thread_id",
        "status",
        "created_at",
        "finished_at",
        "query_summary",
        "schedule_attribution",
    }
    # status 六词表原值直出
    assert [r["status"] for r in runs] == ["done", "waiting_approval", "running"]
    # query_summary：正常透传 / 截 80（[:79]+"…"）/ 缺 run.start → None
    assert runs[2]["query_summary"] == "查一下工单"
    assert runs[1]["query_summary"] is not None
    assert len(runs[1]["query_summary"]) == 80 and runs[1]["query_summary"].endswith("…")
    assert runs[0]["query_summary"] is None
    # fires 表未落地（R-P3-T4-1 降级）→ 归因 None 且端点不炸
    assert all(r["schedule_attribution"] is None for r in runs)
    assert runs[0]["finished_at"] is not None and runs[1]["finished_at"] is None
    assert runs[0]["thread_id"] == tid


@_DB_SKIP
async def test_runs_list_404_matrix(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    prefix, add = seed
    tid = f"{prefix}-th"
    await add(OpsLgRagThread(id=tid, user_id=MAINTAINER_ID))
    # 未知 thread → 404
    resp = await client.get(_RUNS.format(tid=f"{prefix}-nope"))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Thread not found"
    # 属主访问零 runs thread → 200 空列表
    resp = await client.get(_RUNS.format(tid=tid))
    assert resp.status_code == 200
    assert resp.json()["data"] == {"runs": [], "next_cursor": None}


@_DB_SKIP
async def test_runs_list_cross_user_404(
    client: AsyncClient, override_auth_viewer: None, seed: tuple
) -> None:
    prefix, add = seed
    tid = f"{prefix}-th"
    await add(OpsLgRagThread(id=tid, user_id=MAINTAINER_ID))
    resp = await client.get(_RUNS.format(tid=tid))
    assert resp.status_code == 404  # 不 403，不泄存在性
    assert resp.json()["detail"] == "Thread not found"


@_DB_SKIP
async def test_runs_list_unauthenticated_401(client: AsyncClient, seed: tuple) -> None:
    prefix, _ = seed
    resp = await client.get(_RUNS.format(tid=f"{prefix}-th"))
    assert resp.status_code == 401


@_DB_SKIP
async def test_runs_list_pagination_keyset(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    prefix, add = seed
    tid = f"{prefix}-th"
    await add(OpsLgRagThread(id=tid, user_id=MAINTAINER_ID))
    rids = [f"{prefix}-r{i:02d}" for i in range(25)]
    await add(
        *[
            _run(rid, MAINTAINER_ID, tid, "done", _BASE_TS + timedelta(minutes=i))
            for i, rid in enumerate(rids)
        ]
    )
    # 默认页 20
    resp = await client.get(_RUNS.format(tid=tid))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["runs"]) == 20
    assert data["next_cursor"]
    page1_ids = [r["run_id"] for r in data["runs"]]
    assert page1_ids == list(reversed(rids))[0:20]  # created_at desc
    # 第二页 5 · 跨页不重不漏
    resp2 = await client.get(_RUNS.format(tid=tid), params={"cursor": data["next_cursor"]})
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert [r["run_id"] for r in data2["runs"]] == list(reversed(rids))[20:]
    assert data2["next_cursor"] is None
    assert not set(page1_ids) & {r["run_id"] for r in data2["runs"]}
    # limit=7 三页翻尽
    seen: list[str] = []
    cursor = None
    for expected in (7, 7, 7, 4):
        params: dict[str, Any] = {"limit": 7}
        if cursor:
            params["cursor"] = cursor
        page = (await client.get(_RUNS.format(tid=tid), params=params)).json()["data"]
        assert len(page["runs"]) == expected
        seen.extend(r["run_id"] for r in page["runs"])
        cursor = page["next_cursor"]
    assert cursor is None
    assert seen == list(reversed(rids))


@_DB_SKIP
async def test_runs_list_limit_and_cursor_422(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    prefix, add = seed
    tid = f"{prefix}-th"
    await add(OpsLgRagThread(id=tid, user_id=MAINTAINER_ID))
    assert (await client.get(_RUNS.format(tid=tid), params={"limit": 51})).status_code == 422
    assert (await client.get(_RUNS.format(tid=tid), params={"limit": 0})).status_code == 422
    # 坏 cursor：非 base64 / 合法 base64 但缺键 → 均 422
    assert (await client.get(_RUNS.format(tid=tid), params={"cursor": "!!!bad"})).status_code == 422
    import base64 as _b64

    wrong_keys = _b64.urlsafe_b64encode(b'{"foo":1}').decode().rstrip("=")
    assert (await client.get(_RUNS.format(tid=tid), params={"cursor": wrong_keys})).status_code == 422


@_DB_SKIP
async def test_runs_list_schedule_attribution(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    """归因路径：P3-T2 真表已落地——插真行断言三元组后删行（原 R-P3-T4-1
    DROP/CREATE 临时表面在双波汇合后作废：DROP 会删掉 T2 真表炸后续测试）。"""
    prefix, add = seed
    tid = f"{prefix}-th"
    rid_hit, rid_miss = f"{prefix}-rh", f"{prefix}-rm"
    schedule_id = str(uuid.uuid4())
    fire_id = str(uuid.uuid4())
    await add(OpsLgRagThread(id=tid, user_id=MAINTAINER_ID))
    await add(
        _run(rid_hit, MAINTAINER_ID, tid, "done", _BASE_TS),
        _run(rid_miss, MAINTAINER_ID, tid, "done", _BASE_TS + timedelta(minutes=1)),
    )
    async with AsyncSessionLocal() as db:
        await db.execute(
            text(
                "INSERT INTO ops_schedules (schedule_id, tenant_id, user_id, thread_id, "
                "name, instruction, schedule_kind, next_fire_at, timezone, "
                "catchup_policy, status, fire_count, created_at, updated_at) "
                "VALUES (:sid, :tenant, :uid, :tid, :name, :instr, 'interval', now(), "
                "'Asia/Shanghai', 'fire_once', 'active', 0, now(), now())"
            ),
            {
                "sid": schedule_id,
                "tenant": "ops-desk-pilot",
                "uid": MAINTAINER_ID,
                "tid": tid,
                "name": "晨报巡检",
                "instr": "巡检",
            },
        )
        await db.execute(
            text(
                "INSERT INTO ops_schedule_fires "
                "(id, schedule_id, tenant_id, planned_fire_at, run_id, status, fired_at) "
                "VALUES (:fid, :sid, :tenant, now(), :rid, 'fired', now())"
            ),
            {"fid": fire_id, "sid": schedule_id, "tenant": "ops-desk-pilot", "rid": rid_hit},
        )
        await db.commit()
    try:
        resp = await client.get(_RUNS.format(tid=tid))
        assert resp.status_code == 200, resp.text
        runs = {r["run_id"]: r for r in resp.json()["data"]["runs"]}
        assert runs[rid_hit]["schedule_attribution"] == {
            "schedule_id": schedule_id,
            "name": "晨报巡检",
            "fire_id": fire_id,
        }
        assert runs[rid_miss]["schedule_attribution"] is None
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("DELETE FROM ops_schedule_fires WHERE id = :fid"), {"fid": fire_id}
            )
            await db.execute(
                text("DELETE FROM ops_schedules WHERE schedule_id = :sid"),
                {"sid": schedule_id},
            )
            await db.commit()


# ---------------------------------------------------------------------------
# §3.2 run events
# ---------------------------------------------------------------------------


@_DB_SKIP
async def test_events_whitelist_filters_internal_types(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    """白名单 8 值全透传；词表外类型（internal.debug/token）落库后不落响应。"""
    prefix, add = seed
    tid = f"{prefix}-th"
    rid = f"{prefix}-r1"
    rows = [
        _ev(rid, i + 1, MAINTAINER_ID, tid, et, {"k": et}, _BASE_TS + timedelta(seconds=i))
        for i, et in enumerate(_ALLOWED_8)
    ]
    rows += [
        _ev(rid, 9, MAINTAINER_ID, tid, "internal.debug", {"secret": True}, _BASE_TS),
        _ev(rid, 10, MAINTAINER_ID, tid, "token", {"delta": "x"}, _BASE_TS),
    ]
    await add(*rows)
    resp = await client.get(_EVENTS.format(rid=rid))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["run_id"] == rid
    assert [ev["event_type"] for ev in data["events"]] == _ALLOWED_8  # seq 升序
    assert [ev["seq"] for ev in data["events"]] == list(range(1, 9))
    # 事件对象仅四字段
    assert all(set(ev.keys()) == {"seq", "event_type", "payload", "created_at"} for ev in data["events"])
    assert data["events"][0]["payload"] == {"k": "run.start"}
    assert isinstance(data["events"][0]["created_at"], str)
    assert data["truncated"] is False
    assert data["next_after_seq"] is None


@_DB_SKIP
async def test_events_truncation_and_after_seq(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    """505 白名单帧 → 500 帧 + truncated + next_after_seq；续拉取余 5 帧。"""
    prefix, add = seed
    tid = f"{prefix}-th"
    rid = f"{prefix}-r1"
    await add(
        *[
            _ev(rid, i, MAINTAINER_ID, tid, "node.progress", {"i": i}, _BASE_TS + timedelta(seconds=i))
            for i in range(1, 506)
        ]
    )
    resp = await client.get(_EVENTS.format(rid=rid))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["events"]) == 500
    assert data["truncated"] is True
    assert data["next_after_seq"] == 500
    assert data["events"][-1]["seq"] == 500
    resp2 = await client.get(_EVENTS.format(rid=rid), params={"after_seq": data["next_after_seq"]})
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert [ev["seq"] for ev in data2["events"]] == [501, 502, 503, 504, 505]
    assert data2["truncated"] is False
    assert data2["next_after_seq"] is None
    # after_seq 负值 → 422
    assert (await client.get(_EVENTS.format(rid=rid), params={"after_seq": -1})).status_code == 422


@_DB_SKIP
async def test_events_404_matrix(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    prefix, add = seed
    tid = f"{prefix}-th"
    rid_owner = f"{prefix}-r1"
    rid_empty = f"{prefix}-r2"
    await add(
        _ev(rid_owner, 1, MAINTAINER_ID, tid, "run.start", {}, _BASE_TS),
        _run(rid_empty, MAINTAINER_ID, tid, "running", _BASE_TS),
    )
    # 未知 run → 404
    resp = await client.get(_EVENTS.format(rid=f"{prefix}-nope"))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Run not found"
    # run 行存在但零事件帧 → assert_run_owned 真源=事件表 → 404（既有语义）
    resp2 = await client.get(_EVENTS.format(rid=rid_empty))
    assert resp2.status_code == 404


@_DB_SKIP
async def test_events_cross_user_404(
    client: AsyncClient, override_auth_viewer: None, seed: tuple
) -> None:
    prefix, add = seed
    tid = f"{prefix}-th"
    rid = f"{prefix}-r1"
    await add(_ev(rid, 1, MAINTAINER_ID, tid, "run.start", {}, _BASE_TS))
    resp = await client.get(_EVENTS.format(rid=rid))
    assert resp.status_code == 404  # 不 403，不泄存在性


@_DB_SKIP
async def test_events_unauthenticated_401(client: AsyncClient, seed: tuple) -> None:
    prefix, _ = seed
    resp = await client.get(_EVENTS.format(rid=f"{prefix}-r1"))
    assert resp.status_code == 401


@_DB_SKIP
async def test_events_only_internal_frames_empty_200(
    client: AsyncClient, override_auth_maintainer: None, seed: tuple
) -> None:
    """run 仅词表外帧：归属成立（事件表有帧）→ 200 空 events（白名单全滤）。"""
    prefix, add = seed
    tid = f"{prefix}-th"
    rid = f"{prefix}-r1"
    await add(
        _ev(rid, 1, MAINTAINER_ID, tid, "internal.debug", {"x": 1}, _BASE_TS),
        _ev(rid, 2, MAINTAINER_ID, tid, "token", {"delta": "y"}, _BASE_TS),
    )
    resp = await client.get(_EVENTS.format(rid=rid))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["events"] == []
    assert data["truncated"] is False
    assert data["next_after_seq"] is None
