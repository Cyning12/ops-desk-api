"""熔断（P1）的**配置级**闸门检查。

为什么单有单测不够
------------------
R12 在红线层用假传输证明了三态逻辑。但那是在单测装置里，证明不了两件事：

1. **运维真的按得下去**：env 名对不对、阈值改了有没有生效、
   总开关 ``OPS_CAPABILITY_CB_ENABLED=0`` 能不能一键摘掉。
2. **熔断生效时真的零出网**：这里把 ``OA_BASE`` 指向**没人监听**的端口，
   只要请求出门必然是连接失败（``upstream_error``），绝不会是 ``circuit_open``
   ——这个区分就是"零出网"的证据。

四项检查：

1. 连续环境类失败 → open → 后续零出网（错误是 circuit_open，不是连接失败）
2. 恢复时长到点 → 放行一次探测（拨表，不 sleep）
3. **业务类失败不熔断**（★ 最容易被写错的一条）
4. 总开关关掉 → 熔断彻底不生效（摘得掉，才是能上线的兜底）

退出码：0 全部成立；1 有条目不成立。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# 故意指一个**没人监听**的端口：请求真出门 = ConnectionRefused，
# 被熔断挡住 = circuit_open。两者绝不会混淆。
os.environ["OA_BASE"] = "http://127.0.0.1:1"
os.environ.setdefault("OPS_CAP_CRED_OA_GATEWAY_TOKEN", "local-dev-token")
os.environ["OPS_CAPABILITY_CB_FAIL_MAX"] = "3"
os.environ["OPS_CAPABILITY_CB_RESET_TIMEOUT"] = "60"
os.environ["OPS_CAPABILITY_CB_SCOPE"] = "capability"

from app.ops.capability import circuit, invoke  # noqa: E402
from app.ops.capability.gateway import get_registry  # noqa: E402
from app.ops.capability.manifest import reload_capability_manifest  # noqa: E402

problems: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' · ' + detail) if detail else ''}")
    if not ok:
        problems.append(f"{label}: {detail}")


def main() -> int:
    reload_capability_manifest()
    entry = get_registry().get("oa.doc.search")
    if entry is None:
        print("  [FAIL] 清单里找不到 oa.doc.search（能力清单没加载？）")
        return 1
    spec = entry[0]

    circuit.reset()
    ctx = {"tenant_id": "acceptance"}

    # ---- 1) 连续失败 → open → 零出网 ----
    for _ in range(3):
        invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    cb = circuit.breaker_for(spec)
    blocked = invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    err = str(blocked.error or "")
    check(
        "熔断生效 → 零出网（错误是 circuit_open 而非连接失败）",
        cb.current_state == "open"
        and blocked.ok is False
        and "circuit_open" in err
        and blocked.meta.get("blocked") == "circuit",
        f"state={cb.current_state} error={err!r}",
    )

    # ---- 2) 恢复时长到点 → 放行探测（拨表，不 sleep）----
    circuit.advance(spec, 61)
    probed = invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    err2 = str(probed.error or "")
    check(
        "60s 到点 → 放行一次探测（请求真出门，表现为连接失败）",
        "circuit_open" not in err2,
        f"error={err2!r}",
    )

    # ---- 3) 业务类失败不熔断（★）----
    circuit.reset()
    os.environ["OPS_CAPABILITY_CB_FAIL_MAX"] = "2"
    # 参数校验失败（业务/装配类）：打 6 次也必须始终闭合
    for _ in range(6):
        invoke("oa.doc.search", {}, ctx=dict(ctx))  # 缺 keyword → args_schema_invalid
    cb2 = circuit.breaker_for(spec)
    check(
        "业务类失败不熔断（缺参数打 6 次仍 closed）",
        cb2.current_state == "closed" and cb2.fail_counter == 0,
        f"state={cb2.current_state} counter={cb2.fail_counter}",
    )
    os.environ["OPS_CAPABILITY_CB_FAIL_MAX"] = "3"

    # ---- 4) 总开关关掉 → 熔断彻底不生效 ----
    os.environ["OPS_CAPABILITY_CB_ENABLED"] = "0"
    circuit.reset()
    for _ in range(5):
        invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    check(
        "总开关关闭 → 熔断不生效（能一键摘掉）",
        circuit.enabled() is False,
        f"enabled={circuit.enabled()}",
    )
    os.environ.pop("OPS_CAPABILITY_CB_ENABLED")
    circuit.reset()

    snap = circuit.snapshot()
    print(f"  [INFO] backend={snap['backend']} scope={snap['scope']} "
          f"degraded={snap['degraded']} redis_error={snap['redis_error']}")

    if problems:
        print(f"\n熔断检查不通过：{len(problems)} 项")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n熔断检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
