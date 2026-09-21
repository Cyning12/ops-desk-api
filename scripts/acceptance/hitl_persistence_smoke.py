"""HITL **落库这条线**·本地冒烟（纯 HTTP · 不连 LLM · 不连 mock-oa）。

为什么单独有它：``hitl_approval_loop.sh`` 覆盖的是"挂起 → OA 批准 → 恢复"那条**长**链路，
代价是要 mock-oa jar + 真 LLM。而"申请到底有没有落库、列表端点的 SQL 跑不跑得通"
是**更基础、且彼此独立**的一条线——它坏了，界面上和"正在审批中"长得一模一样，
所以值得有一条不用任何外部依赖的检查。

本脚本只打 agent 侧 HTTP，验四件事：

1. ``POST /hitl/requests`` 建一条（Bearer 机读）
2. ``GET /hitl/requests/{id}`` 查得到（Bearer）
3. ``GET /hitl/requests?status=pending`` ← **真正跑的是 ``DbHitlStore.alist``**
   （签名头鉴权）。这条曾经在 asyncpg 下**每次都抛** ``AmbiguousParameterError``，
   而单测只断言 SQL 字符串子串、从不真跑 —— 这个端点就是它的第一现场。
4. ``POST /hitl/callback`` 批准 → 重复回调必须 **409**（不是 404）

收尾：删掉自己造的那条申请（**没有删除端点**，只能直连库清），并把清了多少条报出来。

由 ``hitl_persistence_smoke.sh`` 调用（它负责起服务、等就绪、收尾杀进程）。
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid

_AGENT_PORT = os.environ.get("AGENT_PORT", "8123")
AGENT = f"http://127.0.0.1:{_AGENT_PORT}/api/ops"
ADMIN = os.environ.get("OPS_ADMIN_SYNC_TOKEN", "").strip()

# 出口代理会把打 127.0.0.1 的请求送到代理去（拿到看不懂的 502）
import urllib.error
import urllib.request

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

failures: list[str] = []
created_ids: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def call(method: str, url: str, body=None, headers=None, expect=(200,)):
    data = (
        json.dumps(body, ensure_ascii=False).encode("utf-8")
        if body is not None
        else None
    )
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with OPENER.open(req, timeout=30) as res:
            raw = res.read().decode("utf-8")
            return res.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {"raw": raw}
        if expect and exc.code not in expect:
            raise
        return exc.code, payload


def _signed(body: bytes) -> dict:
    """签名头：``HMAC-SHA256(secret, "{ts}.{nonce}." + raw_body)``（复用仓内实现）。"""
    from app.ops.hitl.signature import sign

    ts = int(time.time())
    nonce = uuid.uuid4().hex
    return {
        "X-Ops-Timestamp": str(ts),
        "X-Ops-Nonce": nonce,
        "X-Ops-Signature": sign(body=body, timestamp=ts, nonce=nonce),
    }


def _cleanup() -> int:
    """删掉本次造的申请。**报出删了几条**，不静默。"""
    if not created_ids:
        return 0
    import asyncio

    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async def _run() -> int:
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                text("DELETE FROM ops_hitl_requests WHERE id = ANY(:ids)"),
                {"ids": created_ids},
            )
            await db.commit()
            return res.rowcount or 0

    return asyncio.run(_run())


def main() -> int:
    rid = f"hitl_smoke_{uuid.uuid4().hex[:12]}"
    created_ids.append(rid)

    # 0 · 运行时自证：必须真的是 db 模式，否则后面全是在验内存版
    code, info = call("GET", f"{AGENT}/hitl/runtime", headers={"Authorization": f"Bearer {ADMIN}"})
    check("GET /hitl/runtime 可达", code == 200, f"code={code}")
    check("持久化模式 = db（否则验的是内存版）", info.get("mode") == "db", str(info.get("mode")))
    check("回调签名密钥已配置", info.get("callback_secret_configured") is True)

    # 1 · 建一条
    code, created = call(
        "POST",
        f"{AGENT}/hitl/requests",
        body={
            "id": rid,
            "run_id": "smoke-run",
            "thread_id": "smoke-thread",
            "tenant_id": "acme",
            "subtask_id": "smoke-run:2",
            "unlock_subtask_id": "smoke-run:1",
            "blocked_by": "prefix_touch_required",
            "reason": "本地落库冒烟",
        },
        headers={"Authorization": f"Bearer {ADMIN}"},
    )
    got_id = (created.get("request") or {}).get("id", "")
    check("POST /hitl/requests 落库", code == 200 and got_id == rid, f"code={code} id={got_id}")

    # 2 · 单条查得到
    code, row = call(
        "GET", f"{AGENT}/hitl/requests/{rid}", headers={"Authorization": f"Bearer {ADMIN}"}
    )
    check("GET /hitl/requests/{id} 查得到", code == 200 and row.get("status") == "pending",
          f"code={code} status={row.get('status')}")

    # 3 · ★ 列表端点 —— 这里跑的是 alist（曾经在 asyncpg 下必抛）
    code, listed = call(
        "GET", f"{AGENT}/hitl/requests?status=pending", headers=_signed(b"")
    )
    items = (listed.get("items") or listed.get("requests") or []) if isinstance(listed, dict) else []
    ids = [str(r.get("id")) for r in items]
    check("GET /hitl/requests?status=pending 真跑通（alist）", code == 200, f"code={code}")
    check("列表里能看到刚建的那条", rid in ids, f"本批 {len(ids)} 条")

    # 4 · 批准 → 重复回调必须 409
    decision = {"request_id": rid, "decision": "approved", "decision_by": "张三", "note": "冒烟"}
    raw = json.dumps(decision, ensure_ascii=False).encode("utf-8")
    code, cb = call("POST", f"{AGENT}/hitl/callback", body=decision, headers=_signed(raw))
    check("POST /hitl/callback 批准成功", code == 200 and (cb.get("request") or {}).get("status") == "approved",
          f"code={code}")

    code, again = call("POST", f"{AGENT}/hitl/callback", body=decision, headers=_signed(raw),
                       expect=(409,))
    check("重复回调 → 409（不是 404）", code == 409, f"code={code}")

    code, after = call(
        "GET", f"{AGENT}/hitl/requests/{rid}", headers={"Authorization": f"Bearer {ADMIN}"}
    )
    check("审批人落库且中文未乱码", after.get("decision_by") == "张三", repr(after.get("decision_by")))

    print()
    if failures:
        print(f"落库冒烟失败 {len(failures)} 项：{failures}")
        return 1
    print("落库冒烟全部通过")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    finally:
        try:
            n = _cleanup()
            print(f"收尾：删除本次造的申请 {n} 条")
        except Exception as exc:  # 清理失败要报出来，不静默留垃圾
            print(f"收尾清理失败（可能残留 1 条申请）：{exc!r}")
    sys.exit(code)
