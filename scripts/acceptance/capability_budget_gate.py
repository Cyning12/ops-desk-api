"""失控兜底（P0-2）的**配置级**闸门检查。

为什么单有单测不够
------------------
R11 在红线层用假传输证明了"配额和 kill switch 会拦人"。但那是在单测装置里，
证明不了**运维真的按得下去**：环境变量名对不对、前缀匹配对不对、
按下之后是不是**真的零出网**。

这里补的正是这一层：

1. 把 ``OPS_CAPABILITY_KILL_SWITCH`` 设成 ``oa.*`` → 真清单里的能力必须被停用，
   并且**请求根本没出门**（OA_BASE 故意指向没人监听的端口，出门必然是别的错）。
2. 松开开关 → 不再被停用，且错误变成"出门失败"而**不是** disabled
   ——证明拦住它的确实是开关，不是别的什么东西。
3. 把配额压到 1 次写 → 第二次必须被 ``policy_blocked: budget_exhausted`` 拦下。
4. 打印观测快照（limits / scope / 追踪了多少会话）供报告引用。

退出码：0 全部成立；1 有条目不成立。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# 故意指一个**没人监听**的端口：只要请求真出门，必然是连接失败（upstream_error），
# 绝不会是 disabled —— 这个区分就是"零出网"的证据。
os.environ["OA_BASE"] = "http://127.0.0.1:1"
os.environ.setdefault("OPS_CAP_CRED_OA_GATEWAY_TOKEN", "local-dev-token")

from app.ops.capability import budget, invoke  # noqa: E402
from app.ops.capability.gateway import get_registry  # noqa: E402
from app.ops.capability.manifest import reload_capability_manifest  # noqa: E402

problems: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}{(' · ' + detail) if detail else ''}")
    if not ok:
        problems.append(f"{label}: {detail}")


def main() -> int:
    reload_capability_manifest()
    spec = get_registry().get("oa.doc.search")
    if spec is None:
        print("  [FAIL] 清单里找不到 oa.doc.search（能力清单没加载？）")
        return 1
    spec = spec[0]

    ctx = {"tenant_id": "acceptance", "run_id": "acceptance-run"}

    # ---- 1) 按下 kill switch：必须停用 + 零出网 ----
    os.environ["OPS_CAPABILITY_KILL_SWITCH"] = "oa.*"
    killed = invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    err = str(killed.error or "")
    check(
        "kill switch 按下 → 停用",
        killed.ok is False and err.startswith("disabled") and "kill_switch" in err,
        f"error={err!r} blocked={killed.meta.get('blocked')!r}",
    )

    # ---- 2) 松开开关：不再被停用（错误必须是"出门失败"，不是 disabled）----
    os.environ.pop("OPS_CAPABILITY_KILL_SWITCH", None)
    alive = invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    err2 = str(alive.error or "")
    check(
        "kill switch 松开 → 不再被停用（请求真出门）",
        not err2.startswith("disabled"),
        f"error={err2!r}",
    )

    # ---- 3) 配额：压到 1 次调用，第二次必须拦下 ----
    os.environ["OPS_CAPABILITY_MAX_CALLS_PER_SESSION"] = "1"
    os.environ["OPS_CAPABILITY_MAX_WRITES_PER_SESSION"] = "0"
    budget.reset()
    first = invoke("oa.doc.search", {"keyword": "a"}, ctx=dict(ctx))
    second = invoke("oa.doc.search", {"keyword": "b"}, ctx=dict(ctx))
    err3 = str(second.error or "")
    check(
        "配额耗尽 → 拦下",
        second.ok is False
        and err3.startswith("policy_blocked")
        and "budget_exhausted" in err3,
        f"first_error={str(first.error)!r} second_error={err3!r}",
    )
    os.environ.pop("OPS_CAPABILITY_MAX_CALLS_PER_SESSION", None)
    os.environ.pop("OPS_CAPABILITY_MAX_WRITES_PER_SESSION", None)
    budget.reset()

    snap = budget.snapshot()
    print(f"  [INFO] budget 快照 limits={snap['limits']} scope={snap['scope']}")
    print(f"  [INFO] kill_switch={snap['kill_switch']} 拦截 calls={snap['blocked_calls']}")

    if problems:
        print(f"\n失控兜底检查不通过：{len(problems)} 项")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n失控兜底检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
