"""HITL 审批回路·真进程联调驱动（不 import 业务代码，纯 HTTP）。

验证「OA 拉得到申请 → 批完代理侧真收到 → 再次回调被 409 拒 → 恢复端点真驱动」。
两端都是真进程、真 socket：签名头编码 / 中文 body / 状态码这些
只有真联调才暴露的问题，单测（连桩都算）会替你掩盖掉。

恢复端点这一段的期望值**随环境变**，别写死 200：
本联调没开 ``LG_RAG_HTTP_CHECKPOINTER=postgres``（内存 saver 每请求新建），
跨请求恢复不可能成立 ⇒ 正确行为是 **503 显式拒绝**，不是 200 假装成功。
返回 200 就意味着"人点批准、什么都没发生"，比报错难查得多。

由 ``hitl_approval_loop.sh`` 调用（它负责起服务与等就绪）；端口经环境变量传入。
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

_AGENT_PORT = os.environ.get("AGENT_PORT", "8123")
_OA_PORT = os.environ.get("OA_PORT", "18081")
AGENT = f"http://127.0.0.1:{_AGENT_PORT}/api/ops"
OA = f"http://127.0.0.1:{_OA_PORT}/api/v1"
ADMIN = "Bearer admintok"
OA_BEARER = "Bearer local-dev-token"

# 开了 PG checkpointer 时，恢复走的是真 PG 路径（由 .sh 的 HITL_RESUME_PG=1 打开）
_PG_CHECKPOINTER = os.environ.get("LG_RAG_HTTP_CHECKPOINTER", "").strip().lower() == "postgres"

# 出口代理会把打 127.0.0.1 的请求送到代理去（返回看不懂的 502）
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" —— {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def call(method: str, url: str, body=None, headers=None, expect=(200,)):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
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
        payload = {}
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {"raw": raw}
        if expect and exc.code not in expect:
            raise
        return exc.code, payload


def _signed(body: dict) -> dict:
    """给回调请求生成签名头（不 import 业务代码，按 signature.py 的口径自己算）。

    口径：``HMAC-SHA256(secret, "{ts}.{nonce}.".encode() + raw_body)``，
    头名 ``X-Ops-Signature`` / ``X-Ops-Timestamp`` / ``X-Ops-Nonce``。
    """
    import hashlib
    import hmac
    import uuid

    secret = os.environ.get("OPS_HITL_CALLBACK_SECRET", "s3cr3t")
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    mac = hmac.new(
        secret.encode("utf-8"), f"{ts}.{nonce}.".encode() + raw, hashlib.sha256
    ).hexdigest()
    return {
        "X-Ops-Timestamp": ts,
        "X-Ops-Nonce": nonce,
        "X-Ops-Signature": f"sha256={mac}",
    }


def main() -> int:
    # 1 · 代理侧运行时：确认真的落库 + 密钥已配
    code, info = call("GET", f"{AGENT}/hitl/runtime", headers={"Authorization": ADMIN})
    check("代理侧 /hitl/runtime 可达", code == 200, f"code={code}")
    check("持久化=memory（不是 null）", info.get("mode") == "memory", str(info.get("mode")))
    check("回调密钥已配置", info.get("callback_secret_configured") is True)

    # 2 · 造一条待批申请（走管理端点，等价于编排层自动落库）
    code, created = call(
        "POST",
        f"{AGENT}/hitl/requests",
        body={
            "run_id": "e2e-run",
            "thread_id": "e2e-thread",
            "checkpoint_id": "ckpt-e2e",
            "tenant_id": "acme",
            "subtask_id": "e2e-run:2",
            "unlock_subtask_id": "e2e-run:1",
            "blocked_by": "prefix_touch_required",
            "reason": "满足本步需要重跑已执行步骤",
        },
        headers={"Authorization": ADMIN},
    )
    rid = (created.get("request") or {}).get("id", "")
    check("申请已落库", code == 200 and bool(rid), f"id={rid}")

    # 3 · mock-oa 拉待办（签名 GET）
    code, listed = call(
        "GET",
        f"{OA}/approval/requests?status=pending",
        headers={"Authorization": OA_BEARER, "X-Ops-Tenant": "acme"},
    )
    data = listed.get("data") or {}
    items = data.get("items") or []
    ids = [str(row.get("id")) for row in items]
    check("OA 拉得到待批申请", code == 200 and rid in ids, f"ids={ids}")

    # 4 · 缺凭据必须被拒（证明业务面守卫没被绕过）
    #    注意：HTTP 状态码恒为 200，业务成败只看信封里的 code
    _, no_bearer = call("GET", f"{OA}/approval/requests", headers={"X-Ops-Tenant": "acme"})
    check("OA 缺 Bearer 被拒", no_bearer.get("code") == 2003, str(no_bearer.get("code")))

    # 5 · mock-oa 批准（中文审批人 → 进 body，不进头）
    code, decided = call(
        "POST",
        f"{OA}/approval/requests/{rid}/decision",
        body={"decision": "approved", "approver": "张三", "note": "同意重跑已执行步骤"},
        headers={"Authorization": OA_BEARER, "X-Ops-Tenant": "acme"},
    )
    d = decided.get("data") or {}
    check("OA 批准：回调成功", d.get("callback_ok") is True,
          f"status={d.get('callback_status')} err={d.get('callback_error')}")

    # 6 · 代理侧真的收到了（**决定性证据**）
    code, after = call("GET", f"{AGENT}/hitl/requests/{rid}",
                       headers={"Authorization": ADMIN})
    check("代理侧状态=approved", after.get("status") == "approved", str(after.get("status")))
    check("审批人中文未乱码", after.get("decision_by") == "张三", repr(after.get("decision_by")))

    # 7 · 重复回调必须 409，且 mock-oa 要把它跟"申请丢了"区分开
    code, again = call(
        "POST",
        f"{OA}/approval/requests/{rid}/decision",
        body={"decision": "approved", "approver": "李四"},
        headers={"Authorization": OA_BEARER, "X-Ops-Tenant": "acme"},
    )
    d2 = again.get("data") or {}
    check("重复决定 → 409（不是 404）", d2.get("callback_status") == 409,
          f"status={d2.get('callback_status')} err={d2.get('callback_error')}")
    check("本地仍留痕（重试看得出批过）", d2.get("local_decision_recorded") is True)

    # 8 · 假签名直接打代理侧回调 → 401
    code, _ = call(
        "POST",
        f"{AGENT}/hitl/callback",
        body={"request_id": rid, "decision": "approved"},
        headers={
            "X-Ops-Signature": "sha256=" + "0" * 64,
            "X-Ops-Timestamp": str(int(time.time())),
            "X-Ops-Nonce": "fake-nonce",
        },
        expect=(401,),
    )
    check("假签名回调被 401", code == 401, f"code={code}")

    # 9 · 恢复端点：**真驱动**，且不许假装成功
    #
    # 期望值随环境变，别写死 200：
    # - 没开 LG_RAG_HTTP_CHECKPOINTER=postgres（默认）⇒ 内存 saver 每请求新建，
    #   跨请求恢复不可能成立 ⇒ **显式 503**。返回 200 就意味着"人点批准、
    #   什么都没发生"，比报错难查得多。
    # - 开了 PG ⇒ 走真 PG checkpointer；这里造的 thread 没真挂起过 ⇒ **409**
    #   not_interrupted（证明它没把 Command 当成新输入重开一局）。
    if _PG_CHECKPOINTER:
        code, resumed = call("POST", f"{AGENT}/hitl/requests/{rid}/resume",
                             headers={"Authorization": ADMIN}, expect=(409,))
        r = resumed or {}
        detail = str(r.get("detail") or "")
        check("PG 开 ⇒ 未挂起 thread 恢复被 409 拒", code == 409, f"code={code} {detail}")
        check("拒绝原因写明是 interrupt（不是重开一局）",
              "interrupt" in detail.lower(), detail)
    else:
        code, resumed = call("POST", f"{AGENT}/hitl/requests/{rid}/resume",
                             headers={"Authorization": ADMIN}, expect=(503,))
        r = resumed or {}
        detail = str(r.get("detail") or "")
        check("未开 PG ⇒ 恢复显式 503（不假装成功）", code == 503, f"code={code} {detail}")
        check("失败原因写明是 checkpointer 没配", "checkpointer" in detail.lower(), detail)
        # 503 而不是 409，说明"待解锁步骤"这一步**已经解析到了** ——
        # 解析不到会先被 409 拦住（下面那条是它的对照）
        check("503 ⇒ 解锁步骤已解析（不是被 409 拦下）", code == 503, f"code={code}")

    # 9b · 对照：已批准但拿不到 unlock_subtask_id ⇒ 409，且**与 503 区分开**
    #      （开了 PG 时这条同样成立：解析不到解锁步骤，压根走不到 checkpointer）
    code, _blank = call(
        "POST",
        f"{AGENT}/hitl/requests",
        body={"run_id": "e2e-run-b", "thread_id": "e2e-thread-b",
              "subtask_id": "e2e-run-b:2", "unlock_subtask_id": ""},
        headers={"Authorization": ADMIN},
    )
    rid_b = (_blank.get("request") or {}).get("id", "")
    _, _ = call("POST", f"{AGENT}/hitl/callback",
                body={"request_id": rid_b, "decision": "approved", "decision_by": "张三"},
                headers=_signed({"request_id": rid_b, "decision": "approved",
                                 "decision_by": "张三"}))
    code, blank = call("POST", f"{AGENT}/hitl/requests/{rid_b}/resume",
                       headers={"Authorization": ADMIN}, expect=(409, 503))
    check("已批但无解锁步骤 ⇒ 409（与 503 区分）", code == 409,
          f"code={code} {blank.get('detail')}")

    # 9c · 对照：还没决的申请不许恢复
    code, pend = call("POST", f"{AGENT}/hitl/requests",
                      body={"run_id": "e2e-run-c", "thread_id": "e2e-thread-c",
                            "subtask_id": "e2e-run-c:2", "unlock_subtask_id": "e2e-run-c:1"},
                      headers={"Authorization": ADMIN})
    rid_c = (pend.get("request") or {}).get("id", "")
    code, pending_resume = call("POST", f"{AGENT}/hitl/requests/{rid_c}/resume",
                                headers={"Authorization": ADMIN}, expect=(409,))
    check("pending 申请不许恢复 ⇒ 409", code == 409, f"code={code}")

    print()
    if failures:
        print(f"联调失败 {len(failures)} 项：{failures}")
        return 1
    print("联调全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
