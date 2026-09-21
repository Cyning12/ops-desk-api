"""OA 能力出网冒烟（**假设 mock-oa 已在 MOCK_OA_PORT 上跑着**，由 .sh 负责起停）。

验的是**三个配置项真的配对了**：
- `OPS_CAPABILITY_EXTRA_MANIFESTS` → OA 清单进注册表（能力数 5 → 8）
- `OA_BASE`                        → 网关基址（清单里写的是 `base_url: OA_BASE`）
- `OPS_CAP_CRED_OA_GATEWAY_TOKEN`  → 凭证值（清单里只写凭证名）

## ⚠️ 为什么不能拿 ``ok=True`` 当通过判据

``oa.doc.search`` 的清单里**声明了降级**（`action: static`，触发词含 `transport`）。
所以 **mock-oa 没起时，它照样返回 ``ok=True``** —— 只是内容是那句静态兜底
「文档检索服务暂时不可用」。只看 ok 会把"根本没连上"判成通过。

必须同时看三样：``ok is True`` **且** ``meta.degraded`` 为空 **且** ``result.code == 0``。

四种形态实测对照（本脚本失败时会按这张表直接告诉你该去查什么）：

| 情形 | ok | error | degraded.trigger | result.code / tenant |
|---|---|---|---|---|
| **服务没起** | True | — | **transport** | None / None |
| 凭证错 | False | `permission_denied: upstream_code=2003` | — | — |
| `OA_BASE` 空 | False | `upstream_error: 未配置 base_url 环境变量: OA_BASE` | — | — |
| 全对 | True | — | — | `0` / `acme` |
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

_EXPECTED_OA = ("oa.doc.search", "oa.org.whois", "oa.todo.mine")

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def _diagnose(res) -> str:
    """按实测对照表给出"下一步查什么"。"""
    meta = res.meta or {}
    trigger = meta.get("degraded_trigger")
    if trigger == "transport":
        return ("transport 降级 = **根本没连上下游**。查：mock-oa 起了吗？"
                f"端口对不对（当前 OA_BASE={os.environ.get('OA_BASE')}）？出口代理会拦 127.0.0.1 吗？")
    err = str(res.error or "")
    if "permission_denied" in err:
        return ("凭证不匹配。查：OPS_CAP_CRED_OA_GATEWAY_TOKEN 是否等于 mock-oa 侧的 "
                "MOCK_OA_TOKEN（默认 local-dev-token）")
    if "未配置 base_url" in err:
        return "OA_BASE 没设。清单里写的是 base_url: OA_BASE，缺了就走不下去"
    return f"未预期形态：error={err[:120]} meta.degraded={meta.get('degraded')}"


async def main() -> int:
    import app.config  # noqa: F401  ← 必须先 import：不然 .env 不会被 load_dotenv 读进来

    from app.ops.capability import list_capabilities
    from app.ops.capability.manifest import load_extra_manifests_from_env

    load_extra_manifests_from_env()
    ids = [r.capability_id for r in list_capabilities()]
    missing = [c for c in _EXPECTED_OA if c not in ids]
    check(
        "OA 清单已加载（能力数应 ≥ 8）",
        not missing,
        f"共 {len(ids)} 个；缺 {missing}" if missing else f"共 {len(ids)} 个，3 个 OA 能力都在",
    )
    if missing:
        print("\n  ⇒ `OPS_CAPABILITY_EXTRA_MANIFESTS` 没生效（默认只加载 builtin 的 5 个）")
        return 1

    from app.ops.capability.gateway import ainvoke

    res = await ainvoke(
        "oa.doc.search",
        {"keyword": "报销", "top_k": 5},
        ctx={"tenant_id": "acme", "run_id": "smoke", "subtask_id": "smoke:1"},
    )
    meta = res.meta or {}
    out = res.output if isinstance(res.output, dict) else {}
    result = out.get("result") or {}
    data = result.get("data") or {}

    print("\n原始返回：")
    print("  ok =", res.ok, "| error =", res.error)
    print("  degraded =", meta.get("degraded"), "| trigger =", meta.get("degraded_trigger"))
    print("  result.code =", result.get("code"), "| tenant =", data.get("tenant"))
    print("  output._degraded =", bool(out.get("_degraded")))
    print("  items[0] =", json.dumps((data.get("items") or [None])[0], ensure_ascii=False)[:160])
    print()

    check("调用成功", res.ok is True, str(res.error or ""))
    check("**没有走降级**（ok=True 不够，降级也是 True）", not meta.get("degraded"),
          f"trigger={meta.get('degraded_trigger')}")
    check("output 里也没有降级标记", not out.get("_degraded"))
    check("下游业务码 = 0", result.get("code") == 0, repr(result.get("code")))
    check("租户谓词下推可见（隔离的硬证据）", data.get("tenant") == "acme", repr(data.get("tenant")))

    print()
    if failures:
        print(f"OA 出网冒烟失败 {len(failures)} 项：{failures}")
        print("诊断：" + _diagnose(res))
        return 1
    print("OA 出网冒烟全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
