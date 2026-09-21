"""熔断（P1）的**配置级**闸门检查。

为什么单有单测不够
------------------
R12 在红线层用假传输证明了三态逻辑。但那是在单测装置里，证明不了两件事：

1. **运维真的按得下去**：env 名对不对、阈值改了有没有生效、
   总开关 ``OPS_CAPABILITY_CB_ENABLED=0`` 能不能一键摘掉。
2. **熔断生效时真的零出网**：这里把 ``OA_BASE`` 指向**没人监听**的端口，
   只要请求出门必然是连接失败（``upstream_error``），绝不会是 ``circuit_open``
   ——这个区分就是"零出网"的证据。

**为什么要自备一个没有降级声明的探针（重要）**
熔断层断言的是"被熔断挡住的调用必须失败并报 ``circuit_open``"。
如果一个能力**声明了降级**，熔断 open 时它会返回"降级成功"（ok=True + degraded），
于是这条断言永远不成立——**降级会把熔断的观测口径盖掉**。
这不是 bug，是设计：熔断管"打得通吗"，降级管"打不通给什么"。

三个 OA 能力现在**都**声明了降级（业务定的），所以本闸门自己写一份
**不带 fallback 的探针清单**来验熔断本身；降级接管之后的形态由
``capability_fallback_gate.py`` 单独验。探针同样走真网络（OA_BASE 指向
没人监听的端口），所以"零出网"的证据依然成立。

五项检查：

1. 连续环境类失败 → open → 后续零出网（错误是 circuit_open，不是连接失败）
2. 恢复时长到点 → 放行一次探测（拨表，不 sleep）
3. **业务类失败不熔断**（★ 最容易被写错的一条）
4. 总开关关掉 → 熔断彻底不生效（摘得掉，才是能上线的兜底）
5. 声明了降级的能力：熔断 open 时返回降级结果，但 **breaker 状态仍是 open**
   （降级不等于"没事了"，状态才是真信号）

退出码：0 全部成立；1 有条目不成立。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# 故意指一个**没人监听**的端口：请求真出门 = ConnectionRefused，
# 被熔断挡住 = circuit_open。两者绝不会混淆。
os.environ["OA_BASE"] = "http://127.0.0.1:1"
os.environ.setdefault("OPS_CAP_CRED_OA_GATEWAY_TOKEN", "local-dev-token")
os.environ.setdefault(
    "OPS_CAPABILITY_EXTRA_MANIFESTS",
    str(ROOT / "app" / "ops" / "capability" / "manifests" / "oa.readonly.v1.yaml"),
)
os.environ["OPS_CAPABILITY_CB_FAIL_MAX"] = "3"
os.environ["OPS_CAPABILITY_CB_RESET_TIMEOUT"] = "60"
os.environ["OPS_CAPABILITY_CB_SCOPE"] = "capability"

from app.ops.capability import circuit, invoke  # noqa: E402
from app.ops.capability.gateway import get_registry  # noqa: E402
from app.ops.capability.manifest import (  # noqa: E402
    load_capability_manifest,
    reload_capability_manifest,
)

problems: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' · ' + detail) if detail else ''}")
    if not ok:
        problems.append(f"{label}: {detail}")


PROBE_ID = "circuit.probe"


def _load_probe_manifest() -> Path:
    """写一份**不带 fallback** 的探针清单（真 http、真出网、不降级）。

    为什么不能用真业务清单里的能力：它们现在都声明了降级，
    熔断 open 时会被降级接走，"必须报 circuit_open" 这条就永远验不出来。
    """
    import tempfile

    doc = {
        "version": 1,
        "capabilities": [
            {
                "id": PROBE_ID,
                "kind": "http",
                "description": "熔断闸门探针（无降级声明）",
                "when_to_use": "熔断闸门自检",
                "args_schema": {
                    "type": "object",
                    # 必须有 required：第 3 项检查靠"缺参数"造出**业务类**失败
                    "required": ["keyword"],
                    "properties": {"keyword": {"type": "string"}},
                },
                "side_effect": "read",
                "visibility": {"departments": ["all"]},
                "http": {
                    "method": "GET",
                    "base_url": "OA_BASE",
                    "path": "/api/v1/doc/search",
                    "auth": "oa_gateway_token",
                    "query_map": {"q": "{{keyword}}"},
                    "timeout_ms": 2000,
                    "success_when": {"path": "$.code", "in": [0]},
                    "error_map": {"5001": "upstream_error"},
                },
            }
        ],
    }
    path = Path(tempfile.mkdtemp(prefix="cb-probe-")) / "probe.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    reload_capability_manifest()
    # ★ 用**没有降级声明**的探针验熔断（见模块 docstring）
    probe_id = PROBE_ID
    load_capability_manifest(_load_probe_manifest())
    entry = get_registry().get(probe_id)
    if entry is None:
        print(f"  [FAIL] 探针 {probe_id} 没注册上（清单加载失败？）")
        return 1
    spec = entry[0]
    if spec.fallback:
        print(f"  [FAIL] 探针 {probe_id} 不该声明降级")
        return 1

    circuit.reset()
    ctx = {"tenant_id": "acceptance"}

    # ---- 1) 连续失败 → open → 零出网 ----
    for _ in range(3):
        invoke(probe_id, {"keyword": "报销"}, ctx=dict(ctx))
    cb = circuit.breaker_for(spec)
    blocked = invoke(probe_id, {"keyword": "报销"}, ctx=dict(ctx))
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
    probed = invoke(probe_id, {"keyword": "报销"}, ctx=dict(ctx))
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
        invoke(probe_id, {}, ctx=dict(ctx))  # 缺 name → args_schema_invalid
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
        invoke(probe_id, {"keyword": "报销"}, ctx=dict(ctx))
    check(
        "总开关关闭 → 熔断不生效（能一键摘掉）",
        circuit.enabled() is False,
        f"enabled={circuit.enabled()}",
    )
    os.environ.pop("OPS_CAPABILITY_CB_ENABLED")
    circuit.reset()

    # ---- 5) 声明了降级的能力：降级接管了错误，但熔断状态仍然是 open ----
    # 这一条防的是"看到降级成功就以为故障好了"——降级只让用户拿到兜底答案，
    # 下游**依然是坏的**，而唯一诚实反映这件事的是 breaker 状态。
    search = get_registry().get("oa.doc.search")
    if search is not None and search[0].fallback:
        circuit.reset()
        for _ in range(3):
            invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
        cb3 = circuit.breaker_for(search[0])
        covered = invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
        check(
            "降级接管了 circuit_open，但 breaker 状态仍 open（故障没好）",
            cb3.current_state == "open"
            and covered.ok is True
            and covered.meta.get("degraded_trigger") == "circuit_open",
            f"state={cb3.current_state} ok={covered.ok} "
            f"trigger={covered.meta.get('degraded_trigger')}",
        )
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
