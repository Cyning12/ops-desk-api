"""L0 多副本验证 · 双进程 pytest（D2 状态外置 / D4 HITL 跨实例 / D3 对照实测）。

形态钉死（SPEC §4 P1 + task 验收）：

- **两独立 uvicorn 子进程**（tests/dualproc_server.py）共享同一测试 PG、异端口、
  同 env 开关；禁同进程双 app（模块级单例共享 = 假跨实例）。
- 每个跨实例用例**先断言实例归属**（whoami pid/port 对拍），归属断言失败 = FAIL 非 skip。
- 前置配置断言：两进程 LG_RAG_HTTP_CHECKPOINTER=postgres / OPS_HITL_PERSISTENCE=db /
  OPS_CAPABILITY_PERSISTENCE=db 生效（whoami 自证），防「开关没开测了个寂寞」。
- 验证卫生：用户/会话/thread 统一 mr<hex>- 前缀，模块收尾清库并报清理数。

变异检验钩子（默认全关）：

- MR_FORCE_SAME_PROCESS=1  —— 实例 B 指向 A 同进程 ⇒ 归属断言必挂（① 归属可检）；
- MR_B_CHECKPOINTER_OFF=1  —— B 不开 PG checkpointer ⇒ 跨实例 resume 断言必挂（② 外置可检）；
- MR_BUDGET_SINGLE=1       —— budget 实证只打单实例 ⇒ 放大断言必挂（③ 失真可检）。

LLM 替身声明：子进程内 supervisor 图换确定性替身（见 dualproc_server 模块 docstring），
被验证的状态外置链路（PG checkpoint / 事件表 / DbHitlStore / resume 驱动）全真。
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import hmac
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.conftest import DB_AVAILABLE

REPO_ROOT = Path(__file__).resolve().parent.parent

# 子进程管理端凭据（仅测试库 + 随机端口，零外部暴露面）
ADMIN_TOKEN = "mr-admin-tok"
HITL_SECRET = "mr-hitl-secret"
# D3 实证：单实例上限压到 2，两实例合计放行 > 2 才证明「配额按实例数放大」
BUDGET_MAX_CALLS = "2"

READY_TIMEOUT_S = 90.0
HTTP_TIMEOUT_S = 60.0

# 出口代理会把打 127.0.0.1 的请求送去代理（hitl_persistence_smoke 先例同款坑）
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE,
    reason="PostgreSQL 测试库不可用（双进程用例必须真库；跳过 ≠ 通过，见 conftest 告警）",
)


# ---------------------------------------------------------------- HTTP 工具


def _http(
    method: str,
    url: str,
    body: dict | None = None,
    headers: dict | None = None,
    timeout: float = HTTP_TIMEOUT_S,
) -> tuple[int, dict]:
    """最小 JSON HTTP 调用（urllib · 不走代理）；非 2xx 返回 (code, payload) 不抛。"""
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with _OPENER.open(req, timeout=timeout) as res:
            raw = res.read().decode("utf-8")
            return res.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {"raw": raw}
        return exc.code, payload


def _sse_stream(
    port: int, query: str, thread_id: str, token: str
) -> tuple[str, list[dict]]:
    """POST /lg-rag/stream 收全帧；返回 (run_id, frames)（frames = data JSON 序列）。"""
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/ops/lg-rag/stream",
        data=json.dumps(
            {"query": query, "mode": "supervisor", "thread_id": thread_id},
            ensure_ascii=False,
        ).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Cookie", f"ops_session={token}")
    frames: list[dict] = []
    with _OPENER.open(req, timeout=HTTP_TIMEOUT_S) as res:
        assert res.status == 200, f"stream HTTP {res.status}"
        run_id = res.headers.get("X-Ops-Lg-Rag-Run-Id") or ""
        for raw in res:
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("data:"):
                frames.append(json.loads(line[5:].strip()))
    assert run_id, "响应头缺 X-Ops-Lg-Rag-Run-Id"
    return run_id, frames


def _replay(
    port: int, run_id: str, token: str, after_seq: int = 0
) -> tuple[int, list[dict]]:
    """POST /lg-rag/replay；返回 (HTTP code, frames)。404 时 frames 为空。"""
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/ops/lg-rag/replay",
        data=json.dumps({"run_id": run_id, "after_seq": after_seq}).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Cookie", f"ops_session={token}")
    frames: list[dict] = []
    try:
        with _OPENER.open(req, timeout=HTTP_TIMEOUT_S) as res:
            for raw in res:
                line = raw.decode("utf-8", "replace").strip()
                if line.startswith("data:"):
                    frames.append(json.loads(line[5:].strip()))
            return res.status, frames
    except urllib.error.HTTPError as exc:
        exc.read()
        return exc.code, frames


def _signed(body: bytes) -> dict[str, str]:
    """HMAC 签名头（口径对齐 scripts/acceptance/hitl_approval_loop.py）。"""
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    mac = hmac.new(
        HITL_SECRET.encode("utf-8"), f"{ts}.{nonce}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return {
        "X-Ops-Timestamp": ts,
        "X-Ops-Nonce": nonce,
        "X-Ops-Signature": f"sha256={mac}",
    }


def _whoami(port: int) -> dict:
    code, payload = _http("GET", f"http://127.0.0.1:{port}/__dualproc__/whoami")
    assert code == 200, f"whoami HTTP {code}: {payload}"
    return payload


def assert_distinct_instances(inst_a, inst_b) -> None:
    """实例归属先断言：确认真跨进程。

    断言失败 = 用例 FAIL（**不是 skip**）——「没真跨实例」是本 task 头号静默错，
    跳过会让它看起来像通过。变异检验①（MR_FORCE_SAME_PROCESS=1）就是打这条。
    """
    a = _whoami(inst_a.port)
    b = _whoami(inst_b.port)
    pid_a, pid_b = a["pid"], b["pid"]
    port_a, port_b = a["port"], b["port"]
    assert pid_a != pid_b, f"归属断言失败：两实例同进程 pid={pid_a}（假跨实例 · P2 弃选形态）"
    assert port_a != port_b, f"归属断言失败：两实例同端口 {port_a}"


# ---------------------------------------------------------------- 进程基建


def _free_port() -> int:
    """动态端口（禁固定端口 · failure_paths「双进程 fixture 起停不稳」对策）。"""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _spawn_replica(name: str, *, checkpointer: bool = True) -> SimpleNamespace:
    """起一个 uvicorn 子进程并等就绪（就绪探针 = /health 内容对得上，不是端口在听）。"""
    port = _free_port()
    env = dict(os.environ)
    env.update(
        {
            "OPS_CHAT_TRACER": "",
            "OPS_ADMIN_SYNC_TOKEN": ADMIN_TOKEN,
            "OPS_HITL_CALLBACK_SECRET": HITL_SECRET,
            "OPS_HITL_PERSISTENCE": "db",
            "OPS_CAPABILITY_PERSISTENCE": "db",
            "OPS_CAPABILITY_MAX_CALLS_PER_SESSION": BUDGET_MAX_CALLS,
            "no_proxy": "127.0.0.1,localhost",
            "NO_PROXY": "127.0.0.1,localhost",
        }
    )
    if checkpointer:
        env["LG_RAG_HTTP_CHECKPOINTER"] = "postgres"
    else:
        # 变异② / 负路径 503：必须给**空串**而不是抹掉——子进程 app.config 的
        # load_dotenv 会把 .env 里的开值重新注入（override=False 只认键是否存在），
        # 实测踩到：pop 掉的键被 .env 复活，「未开 checkpointer」变成假的。
        env["LG_RAG_HTTP_CHECKPOINTER"] = ""
    log = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w", prefix=f"dualproc-{name}-", suffix=".log", delete=False
    )
    proc = subprocess.Popen(
        [sys.executable, "-m", "tests.dualproc_server", "--port", str(port), "--name", name],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    inst = SimpleNamespace(name=name, port=port, proc=proc, log_path=log.name)
    deadline = time.monotonic() + READY_TIMEOUT_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        try:
            code, payload = _http("GET", f"http://127.0.0.1:{port}/health", timeout=3.0)
            if code == 200 and payload.get("status") == "ok":
                return inst
        except OSError:
            pass
        time.sleep(0.5)
    import contextlib  # noqa: PLC0415

    tail = ""
    with contextlib.suppress(OSError):
        tail = "\n".join(Path(log.name).read_text().splitlines()[-30:])
    proc.kill()
    raise RuntimeError(f"子进程 {name} 就绪超时/早退（端口 {port}）。日志尾：\n{tail}")


def _stop_replica(inst) -> None:
    """收尾杀进程（terminate → kill 兜底 · failure_paths 对策）。"""
    if inst is None:
        return
    proc = inst.proc
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


# ---------------------------------------------------------------- DB 工具（父进程侧）


def _pg_dsn() -> str:
    """SQLAlchemy DSN → asyncpg DSN；目标库已由 conftest 钉死为 *_test 测试库。"""
    return os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")


async def _db_exec(sql: str, *args) -> str:
    """每次调用新开连接（pytest 各用例 loop 不保证复用，绝不缓存连接）。"""
    import asyncpg  # noqa: PLC0415

    conn = await asyncpg.connect(_pg_dsn())
    try:
        return await conn.execute(sql, *args)
    finally:
        await conn.close()


def _create_user(prefix: str, name: str) -> tuple[str, str]:
    """造一个 viewer 用户 + DB 会话；返回 (user_id, 明文 session token)。"""
    from app.ops.security import hash_token  # noqa: PLC0415

    token = secrets.token_urlsafe(32)
    user_id = uuid.uuid4()
    now = datetime.now(UTC).replace(tzinfo=None)
    expires = now + timedelta(hours=2)
    # created_at/updated_at 只有 ORM 默认（无 server default），裸 SQL 必须显式给
    asyncio.run(
        _db_exec(
            "INSERT INTO ops_users (id, username, role, created_at, updated_at)"
            " VALUES ($1, $2, $3, $4, $5)",
            user_id, f"{prefix}-{name}", "viewer", now, now,
        )
    )
    asyncio.run(
        _db_exec(
            "INSERT INTO ops_sessions"
            " (id, user_id, token_hash, expires_at, created_at, tenant_id)"
            " VALUES ($1, $2, $3, $4, $5, $6)",
            # session 真源须 ∈ ALLOWED_TENANTS；dualproc_server 的 "dualproc" 是 HITL
            # store 字段，不是 session 租户（否则 normalize_tenant → 422 unknown_tenant）
            uuid.uuid4(), user_id, hash_token(token), expires, now, "ops-desk-pilot",
        )
    )
    return str(user_id), token


def _cleanup_db(prefix: str) -> dict[str, int]:
    """造了什么删什么（hitl_persistence_smoke 先例）；返回各表清理数。"""
    counts: dict[str, int] = {}
    like = f"{prefix}-%"
    # checkpoint_writes / checkpoint_blobs 挂在 checkpoints 上，先删子表
    for table, where in (
        ("checkpoint_writes", "thread_id LIKE $1"),
        ("checkpoint_blobs", "thread_id LIKE $1"),
        ("checkpoints", "thread_id LIKE $1"),
        ("ops_lg_rag_run_events", "thread_id LIKE $1"),
        ("ops_hitl_requests", "thread_id LIKE $1"),
        ("ops_lg_rag_turns", "thread_id LIKE $1"),
        ("ops_lg_rag_threads", "id LIKE $1"),
        ("ops_sessions", "user_id IN (SELECT id FROM ops_users WHERE username LIKE $1)"),
        ("ops_users", "username LIKE $1"),
    ):
        status = asyncio.run(_db_exec(f"DELETE FROM {table} WHERE {where}", like))
        counts[table] = int(status.rsplit(" ", 1)[-1])
    return counts


# ---------------------------------------------------------------- 双进程 fixture


@pytest.fixture(scope="module")
def dualproc():
    """两独立 uvicorn 子进程（A/B · 同测试库异端口同开关）+ 两个登录用户。

    变异①：MR_FORCE_SAME_PROCESS=1 时 B 不另起进程、直指 A —— 归属断言必挂。
    变异②：MR_B_CHECKPOINTER_OFF=1 时 B 不开 PG checkpointer —— 跨实例 resume 必挂。
    """
    prefix = f"mr{uuid.uuid4().hex[:8]}"
    inst_a = _spawn_replica(f"{prefix}-a")
    if os.environ.get("MR_FORCE_SAME_PROCESS") == "1":
        inst_b = inst_a  # 变异检验①：同进程 → 归属断言必须 FAIL
    else:
        inst_b = _spawn_replica(
            f"{prefix}-b",
            checkpointer=os.environ.get("MR_B_CHECKPOINTER_OFF") != "1",
        )
    alice_id, alice_token = _create_user(prefix, "alice")
    bob_id, bob_token = _create_user(prefix, "bob")
    ns = SimpleNamespace(
        prefix=prefix,
        a=inst_a,
        b=inst_b,
        alice=SimpleNamespace(id=alice_id, token=alice_token),
        bob=SimpleNamespace(id=bob_id, token=bob_token),
    )
    try:
        yield ns
    finally:
        if inst_b is not inst_a:
            _stop_replica(inst_b)
        _stop_replica(inst_a)
        counts = _cleanup_db(prefix)
        print(f"[dualproc] 收尾清库 {sum(counts.values())} 行：{counts}")


# ---------------------------------------------------------------- D2 状态外置


def test_instance_attribution_and_config(dualproc) -> None:
    """前置：实例归属（pid/port 相异）+ 两进程配置生效（防「开关没开测了个寂寞」）。"""
    assert_distinct_instances(dualproc.a, dualproc.b)
    for inst in (dualproc.a, dualproc.b):
        info = _whoami(inst.port)
        assert info["checkpointer_postgres"] is True, f"{inst.name} checkpointer 未生效"
        assert info["hitl_persistence"]["mode"] == "db", f"{inst.name} hitl store 非 db"
        cap = info["capability_persistence"]
        assert cap["mode"] == "db", f"{inst.name} capability persistence 非 db"
        assert cap["idempotency"]["scope"] == "cross_instance"


def test_concurrent_startup_setup_no_deadlock(dualproc) -> None:
    """两实例并发首跑（各自 apostgres_saver(setup=True) 幂等建表竞态）不死锁。

    checkpointer.py :48-53 docstring 钉死 setup() 幂等可每次传；这里实证并发形态。
    """
    assert_distinct_instances(dualproc.a, dualproc.b)

    def _one(inst, tag: str) -> tuple[str, list[dict]]:
        return _sse_stream(
            inst.port,
            f"{dualproc.prefix} concurrent {tag}",
            f"{dualproc.prefix}-conc-{tag}",
            dualproc.alice.token,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(_one, dualproc.a, "a")
        fut_b = pool.submit(_one, dualproc.b, "b")
        _, frames_a = fut_a.result(timeout=HTTP_TIMEOUT_S)
        _, frames_b = fut_b.result(timeout=HTTP_TIMEOUT_S)
    for inst, frames in ((dualproc.a, frames_a), (dualproc.b, frames_b)):
        types = [f["event_type"] for f in frames]
        assert types[0] == "run.start" and types[-1] == "done", f"{inst.name} 流不完整: {types}"
        assert "answer" in types, f"{inst.name} 无 answer 帧: {types}"


def test_cross_instance_replay(dualproc) -> None:
    """A 起 run → B 经事件表 replay 全程帧（seq 连续 · 归属正确 · 内容一致）。"""
    assert_distinct_instances(dualproc.a, dualproc.b)
    thread_id = f"{dualproc.prefix}-replay"
    run_id, frames_live = _sse_stream(
        dualproc.a.port, f"{dualproc.prefix} 部署为什么失败", thread_id, dualproc.alice.token,
    )
    assert frames_live and frames_live[-1]["event_type"] == "done"

    code, frames_b = _replay(dualproc.b.port, run_id, dualproc.alice.token)
    assert code == 200, f"B replay HTTP {code}"
    seqs = [f["seq"] for f in frames_b]
    assert seqs == list(range(1, len(seqs) + 1)), f"B replay seq 不连续: {seqs}"
    # 内容一致：B 读回的帧与 A live 发出的帧逐帧对拍（事件表跨实例可读实证）
    live_key = [
        (f["seq"], f["event_type"], json.dumps(f["payload"], sort_keys=True))
        for f in frames_live
    ]
    replay_key = [
        (f["seq"], f["event_type"], json.dumps(f["payload"], sort_keys=True))
        for f in frames_b
    ]
    assert replay_key == live_key, "B replay 帧与 A live 帧不一致"
    assert all(f["run_id"] == run_id for f in frames_b)


def test_cross_user_replay_404(dualproc) -> None:
    """他 user replay 别人的 run → 404（assert_run_owned 既有语义跨实例保持）。"""
    assert_distinct_instances(dualproc.a, dualproc.b)
    run_id, frames = _sse_stream(
        dualproc.a.port,
        f"{dualproc.prefix} alice 的 run",
        f"{dualproc.prefix}-own",
        dualproc.alice.token,
    )
    assert frames[-1]["event_type"] == "done"
    # bob 在两实例上都读不到 alice 的 run（归属按 user_id 反查 · event_store :87-95）
    code_b, _ = _replay(dualproc.b.port, run_id, dualproc.bob.token)
    assert code_b == 404, f"B 上 bob replay 应 404，实得 {code_b}"
    code_a, _ = _replay(dualproc.a.port, run_id, dualproc.bob.token)
    assert code_a == 404, f"A 上 bob replay 应 404，实得 {code_a}"


# ---------------------------------------------------------------- D4 HITL 跨实例


def test_hitl_cross_instance_resume(dualproc) -> None:
    """A 挂起 → B 见申请 → B 批准 → B resume **图真的续跑**（不只断 200）。

    断言链：state 推进（resume.state 非空）+ answer 非空 + hitl.resumed/done 帧
    续写同 run_id 且 seq 接 last_seq（不重开不覆盖）。
    """
    assert_distinct_instances(dualproc.a, dualproc.b)
    thread_id = f"{dualproc.prefix}-hitl"
    run_id, frames_a = _sse_stream(
        dualproc.a.port,
        f"[hitl] {dualproc.prefix} 要重跑已执行步骤",
        thread_id,
        dualproc.alice.token,
    )
    waiting = [f for f in frames_a if f["event_type"] == "hitl.waiting"]
    live_types = [f["event_type"] for f in frames_a]
    assert waiting, f"A 流里没等到 hitl.waiting: {live_types}"
    assert frames_a[-1]["event_type"] == "done"
    assert frames_a[-1]["payload"].get("status") == "waiting_approval"
    requests = waiting[0]["payload"].get("requests") or []
    assert requests, "hitl.waiting 帧没带申请（没落库？）"
    req_id = requests[0]["id"]
    last_seq_a = max(f["seq"] for f in frames_a)

    # B 见申请（DbHitlStore 跨实例可读 · 签名头 = OA 视角）
    code, listed = _http(
        "GET",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/hitl/requests?status=pending",
        headers=_signed(b""),
    )
    assert code == 200, f"B 拉待办 HTTP {code}"
    ids = [str(r.get("id")) for r in listed.get("items") or []]
    assert req_id in ids, f"B 看不到 A 挂起的申请 {req_id}（可见 {len(ids)} 条）"

    # B 批准（签名回调）
    decision = json.dumps(
        {
            "request_id": req_id,
            "decision": "approved",
            "decision_by": f"{dualproc.prefix}-approver",
            "note": "双进程实证",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    code, cb = _http(
        "POST",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/hitl/callback",
        body=json.loads(decision),
        headers=_signed(decision),
    )
    assert code == 200 and (cb.get("request") or {}).get("status") == "approved", (
        f"B 批准失败 HTTP {code}: {cb}"
    )

    # B resume —— checkpoint 由 A 落 PG，B 从未见过这个进程内的图：真跨实例恢复
    code, resumed = _http(
        "POST",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/hitl/requests/{req_id}/resume",
        body={},
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    assert code == 200, f"B resume HTTP {code}: {resumed}"
    outcome = resumed.get("resume") or {}
    # 「图真的续跑」三重断言（只断 200 = 用例不合格 · task 钉死）
    assert outcome.get("state"), "resume 后 state 为空（图没真推进）"
    answer = str(outcome.get("answer") or "")
    assert answer, "resume 后 answer 为空（批了但什么都没发生形态）"
    replay_meta = resumed.get("replay") or {}
    assert replay_meta.get("persisted") is True

    # 恢复段事件续写同 run_id 且 seq 接 last_seq（A 侧 replay 全程可见）
    code, frames_full = _replay(dualproc.a.port, run_id, dualproc.alice.token)
    assert code == 200
    seqs = [f["seq"] for f in frames_full]
    assert seqs == list(range(1, len(seqs) + 1)), f"全程 seq 不连续: {seqs}"
    types = [f["event_type"] for f in frames_full]
    assert "hitl.resumed" in types, f"缺 hitl.resumed 帧: {types}"
    idx_resumed = types.index("hitl.resumed")
    resumed_seq = frames_full[idx_resumed]["seq"]
    assert resumed_seq > last_seq_a, f"hitl.resumed seq={resumed_seq} 未接 last_seq={last_seq_a}"
    assert types[-1] == "done"
    assert frames_full[-1]["payload"].get("status") == "resumed"
    assert all(f["run_id"] == run_id for f in frames_full), "恢复段写去了别的 run_id"
    # 恢复段的 answer 终帧也续写在同一 run 里（aggregator → answer 帧）
    answer_frames = [f for f in frames_full[idx_resumed:] if f["event_type"] == "answer"]
    assert answer_frames and answer_frames[-1]["payload"].get("content"), (
        "恢复段无 answer 终帧（replay 看不到批准后的结论）"
    )


def test_resume_wrong_thread_409(dualproc) -> None:
    """负路径：B 以没挂起过的 thread_id resume → 409 not_interrupted（不重开一局）。"""
    assert_distinct_instances(dualproc.a, dualproc.b)
    body = {
        "run_id": f"{dualproc.prefix}-ghost-run",
        "thread_id": f"{dualproc.prefix}-ghost-thread",
        "subtask_id": f"{dualproc.prefix}-ghost:2",
        "unlock_subtask_id": f"{dualproc.prefix}-ghost:1",
        "blocked_by": "prefix_touch_required",
        "reason": "负路径：没挂起过的 thread",
    }
    code, created = _http(
        "POST",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/hitl/requests",
        body=body,
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    req_id = (created.get("request") or {}).get("id", "")
    assert code == 200 and req_id, f"手工建申请失败 HTTP {code}: {created}"

    dec = json.dumps(
        {"request_id": req_id, "decision": "approved",
         "decision_by": f"{dualproc.prefix}-approver"}
    ).encode("utf-8")
    code, _ = _http(
        "POST",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/hitl/callback",
        body=json.loads(dec),
        headers=_signed(dec),
    )
    assert code == 200, f"批准失败 HTTP {code}"

    code, resp = _http(
        "POST",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/hitl/requests/{req_id}/resume",
        body={},
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    assert code == 409, f"没挂起的 thread 恢复应 409，实得 {code}: {resp}"
    assert "interrupt" in str(resp.get("detail") or "").lower()


def test_resume_without_checkpointer_503(dualproc) -> None:
    """负路径：未开 checkpointer 的实例 resume → 503 fail-closed（不假装成功）。

    单开一个 C 实例（LG_RAG_HTTP_CHECKPOINTER 抹掉 · hitl store 仍 db）：
    A 挂起 → C 见申请 → C 批准 → C resume 必须显式 503。
    """
    inst_c = _spawn_replica(f"{dualproc.prefix}-c", checkpointer=False)
    try:
        _, frames_a = _sse_stream(
            dualproc.a.port,
            f"[hitl] {dualproc.prefix} 503 对照",
            f"{dualproc.prefix}-hitl-503",
            dualproc.alice.token,
        )
        waiting = [f for f in frames_a if f["event_type"] == "hitl.waiting"]
        assert waiting, "A 未挂起（前置失败）"
        req_id = waiting[0]["payload"]["requests"][0]["id"]

        code, listed = _http(
            "GET",
            f"http://127.0.0.1:{inst_c.port}/api/ops/hitl/requests?status=pending",
            headers=_signed(b""),
        )
        ids = [str(r.get("id")) for r in (listed.get("items") or [])] if code == 200 else []
        assert req_id in ids, "C 看不到申请（hitl store 不是 db？前置失败）"

        dec = json.dumps(
            {"request_id": req_id, "decision": "approved",
             "decision_by": f"{dualproc.prefix}-approver"}
        ).encode("utf-8")
        code, _ = _http(
            "POST",
            f"http://127.0.0.1:{inst_c.port}/api/ops/hitl/callback",
            body=json.loads(dec),
            headers=_signed(dec),
        )
        assert code == 200, f"C 批准失败 HTTP {code}"

        code, resp = _http(
            "POST",
            f"http://127.0.0.1:{inst_c.port}/api/ops/hitl/requests/{req_id}/resume",
            body={},
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
        )
        assert code == 503, f"未开 checkpointer 恢复应 503，实得 {code}: {resp}"
        assert "checkpointer" in str(resp.get("detail") or "").lower()
    finally:
        _stop_replica(inst_c)


# ---------------------------------------------------------------- D3 对照实测


def test_budget_quota_amplification_across_instances(dualproc) -> None:
    """budget 配额放大实证：2 实例同 session 总放行 > 单实例上限（进程内计数失真）。

    两进程 OPS_CAPABILITY_MAX_CALLS_PER_SESSION=2（BUDGET_MAX_CALLS）。
    同 session 在 A 打满 2 次后，B 还能再放行 2 次 —— 合计 4 > 2。
    变异③：MR_BUDGET_SINGLE=1 只打 A ⇒ 总放行 2 ≯ 2 ⇒ 断言必挂。
    """
    assert_distinct_instances(dualproc.a, dualproc.b)
    session = f"{dualproc.prefix}-sess"

    def _call(inst) -> dict:
        code, payload = _http(
            "POST",
            f"http://127.0.0.1:{inst.port}/__dualproc__/capability-call",
            body={"session_id": session},
        )
        assert code == 200, f"capability-call HTTP {code}: {payload}"
        return payload

    max_calls = int(BUDGET_MAX_CALLS)
    results_a = [_call(dualproc.a) for _ in range(max_calls)]
    single = os.environ.get("MR_BUDGET_SINGLE") == "1"
    target_b = dualproc.a if single else dualproc.b
    results_b = [_call(target_b) for _ in range(max_calls)]

    total_allowed = sum(1 for r in results_a + results_b if r["ok"])
    assert all(r["ok"] for r in results_a), f"A 侧前 {max_calls} 次不应被拦: {results_a}"
    assert total_allowed > max_calls, (
        f"配额放大未实证：两实例同 session 总放行 {total_allowed} ≯ 单实例上限 {max_calls}"
        "（若只打了一个实例，说明测的是单进程内计数）"
    )
    # 单实例内第 max+1 次必须被拦（证明上限本身生效，不是没开闸）
    over = _call(dualproc.a)
    assert over["ok"] is False and "budget_exhausted" in str(over["error"]), (
        f"A 侧超上限未被拦: {over}"
    )


def test_runtime_scope_and_catalog_parity(dualproc) -> None:
    """/runtime scope 自首字段对拍 + /catalog 两实例一致（registry 启动注册零漂移）。

    scope 对拍之外再证**计数真的分家**：session 只打 A，A 的 snapshot 有、B 没有。
    """
    assert_distinct_instances(dualproc.a, dualproc.b)
    auth = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    marker_session = f"{dualproc.prefix}-parity"
    code, _ = _http(
        "POST",
        f"http://127.0.0.1:{dualproc.a.port}/__dualproc__/capability-call",
        body={"session_id": marker_session},
    )
    assert code == 200

    code, rt_a = _http(
        "GET",
        f"http://127.0.0.1:{dualproc.a.port}/api/ops/admin/capability/runtime",
        headers=auth,
    )
    assert code == 200, f"A /runtime HTTP {code}"
    code, rt_b = _http(
        "GET",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/admin/capability/runtime",
        headers=auth,
    )
    assert code == 200, f"B /runtime HTTP {code}"
    # 既有自首：scope=process-local 两实例都如实标注
    assert rt_a["budget"]["scope"] == "process-local"
    assert rt_b["budget"]["scope"] == "process-local"
    # 计数分家实证：只打过 A 的 session 不出现在 B 的进程内计数里
    assert marker_session in rt_a["budget"]["sessions"]
    assert marker_session not in rt_b["budget"]["sessions"], (
        "B 的 budget snapshot 出现了只打过 A 的 session —— 计数不是进程内？！"
    )

    code, cat_a = _http(
        "GET",
        f"http://127.0.0.1:{dualproc.a.port}/api/ops/admin/capability/catalog",
        headers=auth,
    )
    assert code == 200, f"A /catalog HTTP {code}"
    code, cat_b = _http(
        "GET",
        f"http://127.0.0.1:{dualproc.b.port}/api/ops/admin/capability/catalog",
        headers=auth,
    )
    assert code == 200, f"B /catalog HTTP {code}"

    def _ids(cat: dict) -> list[str]:
        return sorted(str(c) for c in cat.get("visible_ids") or [])

    ids_a, ids_b = _ids(cat_a), _ids(cat_b)
    assert ids_a and ids_a == ids_b, (
        f"两实例 /catalog 漂移：A {len(ids_a)} 项 vs B {len(ids_b)} 项 · "
        f"diff={sorted(set(ids_a) ^ set(ids_b))}"
    )
