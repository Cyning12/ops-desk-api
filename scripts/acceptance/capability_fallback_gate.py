"""降级链（P1 · Q3 下半）的**配置级**闸门检查。

为什么单有单测不够
------------------
R13 在红线层用假传输证明了四件事（声明才降级 / 只有下游不可用才降级 /
写能力永不降级 / 链条有界）。但那是在单测装置里，证明不了**真清单上真的接上了**：

1. ``oa.readonly.v1.yaml`` 里那条声明**真的被 loader 读进去了**
   （字段名拼错、YAML 把 ``on`` 解析成布尔——这类问题只在真清单上才会暴露）。
2. OA_BASE 指向**没人监听**的端口 → 返回的是**声明好的兜底**，且带 degraded 标记，
   而不是一个看不懂的连接错误。
3. **熔断 open 时直接走降级**（不用再付一次完整超时），且零出网。
4. 未声明降级的能力（``oa.org.whois``）**仍然明确失败**——
   默认必须是"不降级"，兜底不能变成默认行为。

退出码：0 全部成立；1 有条目不成立。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# 故意指一个**没人监听**的端口：只要请求真出门，必然是连接失败（transport）。
os.environ["OA_BASE"] = "http://127.0.0.1:1"
os.environ.setdefault("OPS_CAP_CRED_OA_GATEWAY_TOKEN", "local-dev-token")
# 本闸门验的是**真清单**，所以要显式挂上 OA 清单（默认不加载外部清单）。
# 用 setdefault：验收脚本里已经 export 过就以脚本为准。
os.environ.setdefault(
    "OPS_CAPABILITY_EXTRA_MANIFESTS",
    str(ROOT / "app" / "ops" / "capability" / "manifests" / "oa.readonly.v1.yaml"),
)

import json  # noqa: E402

from app.ops.capability import circuit, invoke, list_capabilities  # noqa: E402
from app.ops.capability.fallback import cache_snapshot  # noqa: E402
from app.ops.capability.gateway import get_registry  # noqa: E402
from app.ops.capability.manifest import reload_capability_manifest  # noqa: E402
from app.ops.capability.metrics import reset as metrics_reset  # noqa: E402
from app.ops.capability.metrics import snapshot as metrics_snapshot  # noqa: E402

problems: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}{(' · ' + detail) if detail else ''}")
    if not ok:
        problems.append(f"{label}: {detail}")


def main() -> int:
    metrics_reset()
    circuit.reset()
    reload_capability_manifest()

    entry = get_registry().get("oa.doc.search")
    if entry is None:
        print("  [FAIL] 清单里找不到 oa.doc.search（能力清单没加载？）")
        return 1
    spec_search = entry[0]

    # ---- 1) 声明真的被读进来了（不是"写了但没生效"）----
    fb = spec_search.fallback or {}
    check(
        "真清单声明了降级（loader 读到了）",
        bool(fb) and fb.get("action") == "static",
        f"fallback={fb}",
    )

    ctx = {"tenant_id": "acceptance", "run_id": "acceptance-fallback"}

    # ---- 2) 下游不可用 → 声明好的兜底 + 显式标记 ----
    res = invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    check(
        "下游不可用 → 降级成功且带标记",
        res.ok is True
        and res.meta.get("degraded") is True
        and res.meta.get("degraded_action") == "static"
        and res.meta.get("degraded_from") == "oa.doc.search"
        and bool(res.meta.get("degraded_at")),
        f"ok={res.ok} meta={ {k: v for k, v in res.meta.items() if k.startswith('degrad')} }",
    )
    # ★ 真实原因不能丢：降级是"给了替代答案"，不是"问题消失了"
    check(
        "真实原因保留在 degraded_reason（没被兜底盖掉）",
        "upstream_error" in str(res.meta.get("degraded_reason") or ""),
        f"reason={res.meta.get('degraded_reason')!r}",
    )

    # ---- 3) 熔断 open → 直接走降级（trigger 是 circuit_open，且不再付超时）----
    os.environ["OPS_CAPABILITY_CB_FAIL_MAX"] = "2"
    os.environ["OPS_CAPABILITY_CB_RESET_TIMEOUT"] = "60"
    circuit.reset()
    for _ in range(2):
        invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    tripped = circuit.breaker_for(spec_search)
    opened = invoke("oa.doc.search", {"keyword": "报销"}, ctx=dict(ctx))
    check(
        "熔断 open → 降级（trigger=circuit_open，零出网）",
        tripped.current_state == "open"
        and opened.ok is True
        and opened.meta.get("degraded") is True
        and opened.meta.get("degraded_trigger") == "circuit_open",
        f"state={tripped.current_state} trigger={opened.meta.get('degraded_trigger')}",
    )
    os.environ.pop("OPS_CAPABILITY_CB_FAIL_MAX", None)
    os.environ.pop("OPS_CAPABILITY_CB_RESET_TIMEOUT", None)
    circuit.reset()

    # ---- 4) 三条业务声明都生效，且**降级成什么**各不同（是业务定的，不是框架猜的）----
    for cid, args, want in (
        ("oa.org.whois", {"name": "张三"}, "regular_employee"),
        ("oa.todo.mine", {"status": "pending"}, "degraded_unavailable"),
    ):
        r = invoke(cid, args, ctx=dict(ctx))
        blob = json.dumps(r.output or {}, ensure_ascii=False)
        check(
            f"{cid} 按业务声明降级（不是框架猜的）",
            r.ok is True and r.meta.get("degraded") is True and want in blob,
            f"ok={r.ok} action={r.meta.get('degraded_action')} hit={want in blob}",
        )
        # ★ 模型必须看得见：标记要写进 output，不能只留在 meta
        marker = (r.output or {}).get("_degraded") if isinstance(r.output, dict) else None
        check(
            f"{cid} 降级标记写进了工具输出（模型看得见）",
            isinstance(marker, dict) and "不是查询结果" in str(marker.get("notice") or ""),
            f"marker={'有' if marker else '无'}",
        )

    # ---- 5) 反向对照：**业务类失败**（缺参数）不得降级 ----
    # 这条在真清单上验才有意义：参数错换接口也一样错，降级只会多付一次调用
    # 并把真实原因盖掉。
    bad = invoke("oa.doc.search", {}, ctx=dict(ctx))  # 缺 keyword
    check(
        "业务类失败（缺参数）不降级 → 明确失败",
        bad.ok is False
        and bad.meta.get("degraded") is not True
        and "args_schema_invalid" in str(bad.error or ""),
        f"ok={bad.ok} err={str(bad.error)[:60]!r}",
    )

    # ---- 6) 默认确实是不降级：内置五枚能力一律没声明 ----
    specs = list_capabilities()
    builtin_declared = [
        s.capability_id
        for s in specs
        if s.fallback and s.capability_id.startswith(("mock_", "get_", "utc_"))
    ]
    declared = [s.capability_id for s in specs if s.fallback]
    check(
        "默认不降级（内置能力零声明，声明的只有业务显式写的）",
        not builtin_declared and set(declared) == {
            "oa.doc.search",
            "oa.org.whois",
            "oa.todo.mine",
        },
        f"declared={sorted(declared)}",
    )

    # ---- 7) 观测：降级必须在指标里看得见（否则"系统正常"是假的）----
    snap = metrics_snapshot()
    degrade = snap.get("degrade") or {}
    check(
        "指标里有 degrade 计数（降级不会从监控里消失）",
        degrade.get("calls", 0) >= 4 and degrade.get("unmarked", 0) == 0,
        f"degrade={degrade}",
    )
    print(f"  [INFO] 降级缓存 {cache_snapshot()}")
    print(f"  [INFO] by_action={degrade.get('by_action')} by_depth={degrade.get('by_depth')}")

    if problems:
        print(f"\n降级链检查不通过：{len(problems)} 项")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n降级链检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
