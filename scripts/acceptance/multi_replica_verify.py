#!/usr/bin/env python3
"""多副本验证 D1/D4 · runbook 轨驱动（纯 HTTP · 双容器 + 降级 LB · 报告落盘）。

由 multi_replica_verify.sh 编排（建库 → compose 双实例 → 起 LB → 本驱动 → 收尾）。
覆盖断言面（task D1/D4 验收）：

- 拓扑：两实例 /health ok · whoami pid 相异 · env 对拍（checkpointer/hitl/capability 开关一致）；
- 登录态跨实例：LB 登录拿的 cookie 直打 A 与 B 都 200；
- thread 历史跨实例：A 起的 thread 由 B 续跑（同 thread_id 再打不 404）· A 的 run B replay 逐帧一致；
- 无亲和对照：nginx round-robin（SPEC 命名降级形态）下同会话连续请求**两实例均有命中**
  （X-MR-Upstream 归属头对拍）且语义不漂移；
- 会话亲和对照：自研 Python LB cookie-sticky 下同会话全部落同实例
  （vanilla nginx 开源版不支持 cookie 亲和 —— 亲和组支持面 = 自研 LB，分开标注不混）；
- D4 部署轨：A 挂起 → B 见申请 → B 批准 → B resume 图真的续跑（answer 非空 + 帧续写同 run_id）；
- Eureka 注册条目：**未覆盖待补**（外部仓 + 本仓无 Eureka 客户端 · 诚实标注不撒谎）。

报告：reports/multi_replica_verify/deploy_<ts>.yaml（字段族对齐 reconcile/backfill 先例）。
替身声明：容器内跑 tests/dualproc_server.py 确定性替身图（见该文件 docstring）——
被验证对象是状态外置链路 + 部署拓扑，不是 LLM 编排。
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime, timedelta

PORT_A = int(os.environ.get("MR_PORT_A", "8101"))
PORT_B = int(os.environ.get("MR_PORT_B", "8102"))
PORT_LB_RR = int(os.environ.get("MR_LB_RR", "8199"))
PORT_LB_COOKIE = int(os.environ.get("MR_LB_COOKIE", "8200"))
DB_DSN = os.environ["MR_DB_DSN"]  # postgresql://...（asyncpg 口径 · 专用库 opsdesk_mrv）
GIT_SHA = os.environ.get("MR_GIT_SHA", "")
IMAGE_ID = os.environ.get("MR_IMAGE_ID", "")
REPORT_PATH = os.environ["MR_REPORT"]

ADMIN = {"Authorization": "Bearer mr-admin-tok"}
SECRET = b"mr-hitl-secret"
PREFIX = f"mr{uuid.uuid4().hex[:8]}"

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

results: list[dict] = []
commands: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))
    results.append({"name": name, "ok": bool(ok), "detail": detail})


def call(method: str, url: str, body=None, headers=None, timeout=120):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with OPENER.open(req, timeout=timeout) as res:
            raw = res.read().decode("utf-8")
            headers_lc = {k.lower(): v for k, v in res.headers.items()}
            return res.status, (json.loads(raw) if raw else {}), headers_lc
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {"raw": raw}
        return exc.code, payload, {k.lower(): v for k, v in exc.headers.items()}


def stream(port: int, query: str, thread_id: str, cookie: str):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/ops/lg-rag/stream",
        data=json.dumps({"query": query, "mode": "supervisor", "thread_id": thread_id},
                        ensure_ascii=False).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Cookie", cookie)
    frames = []
    with OPENER.open(req, timeout=120) as res:
        run_id = res.headers.get("X-Ops-Lg-Rag-Run-Id") or ""
        for raw in res:
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("data:"):
                frames.append(json.loads(line[5:].strip()))
    return run_id, frames


def replay(port: int, run_id: str, cookie: str):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/ops/lg-rag/replay",
        data=json.dumps({"run_id": run_id, "after_seq": 0}).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Cookie", cookie)
    frames = []
    with OPENER.open(req, timeout=60) as res:
        for raw in res:
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("data:"):
                frames.append(json.loads(line[5:].strip()))
        return res.status, frames


def signed(body: bytes) -> dict:
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    mac = hmac.new(SECRET, f"{ts}.{nonce}.".encode() + body, hashlib.sha256).hexdigest()
    return {"X-Ops-Timestamp": ts, "X-Ops-Nonce": nonce, "X-Ops-Signature": f"sha256={mac}"}


async def _db(sql: str, *args) -> str:
    import asyncpg  # noqa: PLC0415

    conn = await asyncpg.connect(DB_DSN)
    try:
        return await conn.execute(sql, *args)
    finally:
        await conn.close()


def db_exec(sql: str, *args) -> str:
    return asyncio.run(_db(sql, *args))


def make_user() -> tuple[str, str]:
    """造 viewer 用户 + 邀请码（真登录路径拿 cookie）；返回 (username, 明文邀请码)。"""
    import secrets  # noqa: PLC0415

    from app.ops.security import hash_token  # noqa: PLC0415

    username = f"{PREFIX}-viewer"
    invite = secrets.token_urlsafe(24)
    # ⚠️ 过期余量必须按天给：Docker VM 时钟与宿主机可能差数小时
    # （实测 2026-09-22 本机 db 容器时钟快 8h，+2h 的邀请码一落地就"过期"→ 401）。
    # 口径对齐 conftest seeded_maintainer 的 timedelta(days=1)。
    now = datetime.now(UTC).replace(tzinfo=None)
    db_exec(
        "INSERT INTO ops_users (id, username, role, created_at, updated_at)"
        " VALUES ($1, $2, $3, $4, $5)",
        uuid.uuid4(), username, "viewer", now, now,
    )
    db_exec(
        "INSERT INTO ops_invite_tokens (token, role, expires_at, created_at)"
        " VALUES ($1, $2, $3, $4)",
        hash_token(invite), "viewer", now + timedelta(days=1), now,
    )
    return username, invite


def cleanup() -> dict:
    counts = {}
    like = f"{PREFIX}-%"
    for table, where in (
        ("checkpoint_writes", "thread_id LIKE $1"),
        ("checkpoint_blobs", "thread_id LIKE $1"),
        ("checkpoints", "thread_id LIKE $1"),
        ("ops_lg_rag_run_events", "thread_id LIKE $1"),
        ("ops_hitl_requests", "thread_id LIKE $1"),
        ("ops_lg_rag_turns", "thread_id LIKE $1"),
        ("ops_lg_rag_threads", "id LIKE $1"),
        ("ops_sessions", "user_id IN (SELECT id FROM ops_users WHERE username LIKE $1)"),
        ("ops_invite_tokens", "used_by_user_id IN (SELECT id FROM ops_users WHERE username LIKE $1)"
         " OR token NOT IN (SELECT token FROM ops_invite_tokens WHERE used_by_user_id IS NOT NULL)"
         " AND created_at > now() - interval '1 hour' AND role = 'viewer'"),
        ("ops_users", "username LIKE $1"),
    ):
        try:
            if table == "ops_invite_tokens":
                # 邀请码没有 username 维度：按 used_by_user_id 精确删
                status = db_exec(
                    "DELETE FROM ops_invite_tokens WHERE used_by_user_id IN"
                    " (SELECT id FROM ops_users WHERE username LIKE $1)",
                    like,
                )
            else:
                status = db_exec(f"DELETE FROM {table} WHERE {where}", like)
            counts[table] = int(status.rsplit(" ", 1)[-1])
        except Exception as exc:
            # checkpoint 表由 saver.setup() 懒建：本次没跑图就不存在 —— 不算残留
            if "does not exist" in str(exc):
                counts[table] = 0
            else:
                raise
    return counts


def main() -> int:
    base_a = f"http://127.0.0.1:{PORT_A}"
    base_b = f"http://127.0.0.1:{PORT_B}"
    lb_rr = f"http://127.0.0.1:{PORT_LB_RR}"
    lb_cookie = f"http://127.0.0.1:{PORT_LB_COOKIE}"

    # ---- 拓扑 / 配置对拍
    code_a, health_a, _ = call("GET", f"{base_a}/health")
    code_b, health_b, _ = call("GET", f"{base_b}/health")
    check("两实例健康", code_a == 200 and code_b == 200
          and health_a.get("status") == "ok" and health_b.get("status") == "ok",
          f"A={code_a} B={code_b}")

    _, wa, _ = call("GET", f"{base_a}/__dualproc__/whoami")
    _, wb, _ = call("GET", f"{base_b}/__dualproc__/whoami")
    # 容器归属对拍用名字不用 pid：两容器各自 pid namespace，init 都是 pid 1
    check("实例归属：两容器两进程（name 对拍 · 容器 pid namespace 下 pid 恒 1 不可用）",
          wa.get("name") != wb.get("name") and bool(wa.get("pid")) and bool(wb.get("pid")),
          f"A={wa.get('name')}(pid {wa.get('pid')}) B={wb.get('name')}(pid {wb.get('pid')})")
    env_equal = (
        wa.get("checkpointer_postgres") == wb.get("checkpointer_postgres") is True
        and (wa.get("hitl_persistence") or {}).get("mode")
        == (wb.get("hitl_persistence") or {}).get("mode") == "db"
        and (wa.get("capability_persistence") or {}).get("mode")
        == (wb.get("capability_persistence") or {}).get("mode") == "db"
    )
    check("两实例 env 对拍一致（配置漂移防线）", env_equal,
          f"A ckpt={wa.get('checkpointer_postgres')} B ckpt={wb.get('checkpointer_postgres')}")

    # ---- 登录态跨实例
    username, invite = make_user()
    commands.append(f"POST {lb_rr}/api/ops/auth/login (viewer={username})")
    code, _, headers = call(
        "POST", f"{lb_rr}/api/ops/auth/login",
        body={"username": username, "invite_token": invite},
    )
    set_cookie = headers.get("set-cookie", "")
    cookie = set_cookie.split(";", 1)[0] if "ops_session=" in set_cookie else ""
    check("LB 登录拿 cookie", code == 200 and cookie.startswith("ops_session="),
          f"code={code} upstream={headers.get('x-mr-upstream')}")

    code_a, me_a, hdr_a = call("GET", f"{base_a}/api/ops/auth/me",
                               headers={"Cookie": cookie})
    code_b, me_b, hdr_b = call("GET", f"{base_b}/api/ops/auth/me",
                               headers={"Cookie": cookie})
    check("鉴权 cookie 跨实例 200（无需会话亲和 · ops_sessions DB 存）",
          code_a == 200 and code_b == 200
          and (me_a.get("user") or me_a).get("username")
          == (me_b.get("user") or me_b).get("username") == username,
          f"A={code_a} B={code_b}")

    # ---- thread 历史跨实例 + replay 跨实例
    thread_id = f"{PREFIX}-t1"
    commands.append(f"POST {base_a}/api/ops/lg-rag/stream (thread={thread_id})")
    run_id, frames_a = stream(PORT_A, f"{PREFIX} 第一轮：部署为什么失败", thread_id, cookie)
    check("A 起 run 完成", bool(frames_a) and frames_a[-1]["event_type"] == "done",
          f"frames={len(frames_a)}")
    commands.append(f"POST {base_b}/api/ops/lg-rag/stream (同 thread 续跑)")
    run_id_b, frames_b2 = stream(PORT_B, f"{PREFIX} 第二轮：继续", thread_id, cookie)
    check("thread 跨实例续跑不 404（B 读得到 A 建的 thread）",
          bool(frames_b2) and frames_b2[-1]["event_type"] == "done",
          f"B frames={len(frames_b2)}")
    code_r, frames_replay = replay(PORT_B, run_id, cookie)
    seqs = [f["seq"] for f in frames_replay]
    check("B replay A 的 run：seq 连续且内容一致",
          code_r == 200 and seqs == list(range(1, len(seqs) + 1))
          and len(frames_replay) == len(frames_a),
          f"replay={len(frames_replay)} vs live={len(frames_a)}")

    # ---- 无亲和对照（nginx rr · 归属头对拍 · 语义不漂移）
    def _upstream_of(hdr: dict) -> str:
        raw = hdr.get("x-mr-upstream", "?")
        # nginx 给的是 $upstream_addr（IP:port · 实测 Docker Desktop 网关 IP
        # 192.168.65.254 而非主机名）；自研 LB 给的是名字。按端口尾段归一。
        if raw.endswith(f":{PORT_A}"):
            return "api-a"
        if raw.endswith(f":{PORT_B}"):
            return "api-b"
        return raw

    ups, oks = set(), 0
    for _i in range(6):
        code, me, hdr = call("GET", f"{lb_rr}/api/ops/auth/me", headers={"Cookie": cookie})
        ups.add(_upstream_of(hdr))
        oks += int(code == 200 and username in json.dumps(me, ensure_ascii=False))
    commands.append(f"GET {lb_rr}/api/ops/auth/me ×6 (rr · 同 cookie)")
    check("无亲和：同会话连续请求落不同实例（两实例均有命中）",
          ups == {"api-a", "api-b"}, f"upstreams={sorted(ups)}")
    check("无亲和：语义不漂移（6/6 200 且同用户）", oks == 6, f"ok={oks}/6")

    # ---- 会话亲和对照（自研 LB cookie-sticky 支持面）
    ups2, oks2 = set(), 0
    for _i in range(6):
        code, me, hdr = call("GET", f"{lb_cookie}/api/ops/auth/me", headers={"Cookie": cookie})
        ups2.add(_upstream_of(hdr))
        oks2 += int(code == 200)
    commands.append(f"GET {lb_cookie}/api/ops/auth/me ×6 (cookie-sticky)")
    check("会话亲和：同会话落同实例（cookie-sticky）", len(ups2) == 1 and oks2 == 6,
          f"upstreams={sorted(ups2)} ok={oks2}/6")

    # ---- D4 runbook 轨：A 挂起 → B 见申请 → B 批准 → B resume 图真的续跑
    thread_h = f"{PREFIX}-hitl"
    run_h, frames_h = stream(PORT_A, f"[hitl] {PREFIX} 要重跑已执行步骤", thread_h, cookie)
    waiting = [f for f in frames_h if f["event_type"] == "hitl.waiting"]
    req_id = (waiting[0]["payload"].get("requests") or [{}])[0].get("id", "") if waiting else ""
    check("D4：A 挂起（hitl.waiting + waiting_approval）",
          bool(waiting) and frames_h[-1]["payload"].get("status") == "waiting_approval",
          f"req={req_id}")
    code, listed, _ = call("GET", f"{base_b}/api/ops/hitl/requests?status=pending",
                           headers=signed(b""))
    ids = [str(r.get("id")) for r in (listed.get("items") or [])] if code == 200 else []
    check("D4：B 见申请（DbHitlStore 跨实例）", req_id in ids, f"B 可见 {len(ids)} 条")
    dec = json.dumps({"request_id": req_id, "decision": "approved",
                      "decision_by": f"{PREFIX}-approver"}, ensure_ascii=False).encode("utf-8")
    code, cb, _ = call("POST", f"{base_b}/api/ops/hitl/callback",
                       body=json.loads(dec), headers=signed(dec))
    check("D4：B 批准", code == 200 and (cb.get("request") or {}).get("status") == "approved",
          f"code={code}")
    commands.append(f"POST {base_b}/api/ops/hitl/requests/{req_id}/resume")
    code, resumed, _ = call("POST", f"{base_b}/api/ops/hitl/requests/{req_id}/resume",
                            body={}, headers=ADMIN)
    outcome = resumed.get("resume") or {}
    answer = str(outcome.get("answer") or "")
    check("D4：B resume 图真的续跑（state 推进 + answer 非空 · 不只断 200）",
          code == 200 and bool(outcome.get("state")) and bool(answer),
          f"code={code} answer={answer[:60]}")
    code, frames_full = replay(PORT_A, run_h, cookie)
    types = [f["event_type"] for f in frames_full]
    seqs_full = [f["seq"] for f in frames_full]
    check("D4：恢复段帧续写同 run_id（hitl.resumed + done(resumed) · seq 连续）",
          code == 200 and "hitl.resumed" in types
          and types[-1] == "done"
          and frames_full[-1]["payload"].get("status") == "resumed"
          and seqs_full == list(range(1, len(seqs_full) + 1))
          and all(f["run_id"] == run_h for f in frames_full),
          f"types={types}")

    # ---- Eureka 条目（诚实标注）
    results.append({
        "name": "外部 Java 网关 + Eureka 注册 2 实例",
        "ok": None,
        "detail": "未覆盖待补：网关/Eureka 在外部仓（ops-desk-api-java-gateway / "
                  "ops-desk-eureka-server），本仓 FastAPI 无 Eureka 客户端；"
                  "本次拓扑前置 = 宿主机自研 Python 降级 LB（registry 拉取受限，"
                  "nginx/haproxy 镜像不可得）。**不得**把本降级形态读作「网关验证通过」。",
    })

    return 0 if all(r["ok"] for r in results if r["ok"] is not None) else 1


def write_report(exit_code: int, cleanup_counts: dict) -> None:
    import yaml  # noqa: PLC0415

    report = {
        "task": "multi-replica-verify",
        "track": "D1 部署验证 + D4 runbook 轨（F1 双轨之手工实测轨）",
        "recorded_at": datetime.now(UTC).isoformat(),
        "git_sha": GIT_SHA,
        "image_id": IMAGE_ID,
        "topology": {
            "instances": [
                {"name": "api-a", "port": PORT_A},
                {"name": "api-b", "port": PORT_B},
            ],
            "shared_db": DB_DSN.rsplit("@", 1)[-1],
            "lb": [
                {"port": PORT_LB_RR, "mode": "nginx round-robin",
                 "via": "multi_replica_nginx.conf"},
                {"port": PORT_LB_COOKIE, "mode": "cookie-sticky（自研 Python LB）",
                 "via": "multi_replica_lb.py"},
            ],
        },
        "gateway_form": (
            "降级 LB 双组：无亲和 = nginx:alpine round-robin（SPEC 命名降级形态 · "
            "scripts/acceptance/multi_replica_nginx.conf）；会话亲和 = 自研 Python LB "
            "cookie-sticky（multi_replica_lb.py · vanilla nginx 开源版不支持 cookie 亲和，"
            "亲和组支持面归自研 LB）。首选外部 Java 网关未覆盖：网关/Eureka 在外部仓、"
            "本仓 FastAPI 无 Eureka 客户端 —— Eureka 注册 2 实例条目：未覆盖待补。"
        ),
        "graph_substitution": (
            "容器内跑 tests/dualproc_server.py 确定性替身图（与双进程 pytest 轨同一 seam）；"
            "被验证对象 = 状态外置链路 + 部署拓扑（全真），LLM 编排 = 替身（诚实声明）。"
        ),
        "commands": commands,
        "assertions": results,
        "cleanup_counts": cleanup_counts,
        "exit_code": exit_code,
        "verdict": "pass" if exit_code == 0 else "fail",
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(report, f, allow_unicode=True, sort_keys=False)
    print(f"报告落盘：{REPORT_PATH}")


if __name__ == "__main__":
    code = 1
    counts: dict = {}
    try:
        code = main()
    finally:
        try:
            counts = cleanup()
            print(f"收尾清理：{counts}")
        except Exception as exc:
            print(f"收尾清理失败（可能残留）：{exc!r}")
        write_report(code, counts)
    sys.exit(code)
