"""HITL 审批回路·真进程联调驱动（不 import 业务代码，纯 HTTP）。

验证「OA 拉得到申请 → 批完代理侧真收到 → 再次回调被 409 拒 → 可恢复点解锁」。
两端都是真进程、真 socket：签名头编码 / 中文 body / 状态码这些
只有真联调才暴露的问题，单测（连桩都算）会替你掩盖掉。

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

    # 9 · 恢复端点：只有 approved 才能 resume
    code, resumed = call("POST", f"{AGENT}/hitl/requests/{rid}/resume",
                         headers={"Authorization": ADMIN}, expect=(200, 409))
    r = resumed or {}
    check("resume 给出解锁步骤", code == 200 and r.get("unlock_subtask_id") == "e2e-run:1",
          str(r.get("unlock_subtask_id")))
    check("resume 带着 checkpoint 标识", r.get("thread_id") == "e2e-thread"
          and r.get("checkpoint_id") == "ckpt-e2e")

    print()
    if failures:
        print(f"联调失败 {len(failures)} 项：{failures}")
        return 1
    print("联调全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
