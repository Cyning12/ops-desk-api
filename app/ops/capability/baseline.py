"""平台级可见集基线（按业务域逐批放开新 kind）。

**为什么要有这个模块**：`strategy_builder` 与 `supervisor` 的 filter 原本各写一份
（内容相同），迟早漂移——一处放开、另一处没放开，就变成「Builder 允许但 Supervisor
看不到」或反过来。**单一真相，两处共用。**

**为什么不是一次性放开 kind**：`http` 这类新 kind 一放开，等于把**所有**对外接入的
能力同时交给模型。按**域**逐批放开更稳，而"域"天然落在 `tags` 上：

- 存量 `local_fn`：照旧可见（不受本模块影响）
- 命中 `DOMAIN_ALLOW_TAGS` 的能力：**豁免 kinds 裁剪**（即新 kind 也能被模型看到）
- 新增一个域 = 往 `DOMAIN_ALLOW_TAGS` 加一个 tag

**注意**：这条放宽只作用于 `kinds` 裁剪；`deny_high_risk` / `deny_write` 仍然生效
（``registry._match_filter`` 的判序保证了这一点）。否则一个 tag 就等于换到全部豁免。

配套纪律：能力清单本身还要 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载才会进注册表，
两层「显式打开」是刻意的——放开可见集 ≠ 放开加载。
"""

from __future__ import annotations

import os

from app.ops.capability.types import CapabilityFilter

#: 模型可见的**基础 kind**（进程内能力）。新 kind 不进这里，走域放行。
DEFAULT_KINDS: frozenset[str] = frozenset({"local_fn"})

#: 域放行标签：命中任一 tag 的能力豁免 `DEFAULT_KINDS` 裁剪。
#: 逐批放开的单一入口——加域只改这一行。
DOMAIN_ALLOW_TAGS: frozenset[str] = frozenset({"oa"})

#: 写能力放行标签（env 门控 · testing-write-capability）：命中任一 tag 的
#: 能力**只豁免 `deny_write` 一层**；默认空 = `None` = 判序零 diff。
#: **永不豁免 `deny_high_risk`**（判序在其前，高危写恒裁）。
#: ⚠ 生效时机：`baseline_filter()` **调用时**读取；BUILDER/SUPERVISOR
#: filter 是模块级常量（import 时固化）——env 须在 import app 之前设置，
#: 测试内须显式重建 filter（对齐钉死契约，禁止依赖 import 顺序巧合）。
ENV_ALLOW_WRITE_TAGS = "OPS_CAPABILITY_ALLOW_WRITE_TAGS"


def _allow_write_tags_from_env() -> frozenset[str] | None:
    """读 `OPS_CAPABILITY_ALLOW_WRITE_TAGS`（逗号分隔）；空/未设 → None。"""
    raw = os.environ.get(ENV_ALLOW_WRITE_TAGS, "")
    tags = frozenset(t.strip() for t in raw.split(",") if t.strip())
    return tags or None


def baseline_filter(*, node_role: str) -> CapabilityFilter:
    """给模型看的可见集基线（Builder 与 Supervisor 共用）。"""
    return CapabilityFilter(
        node_role=node_role,
        kinds=DEFAULT_KINDS,
        allow_tags_any=DOMAIN_ALLOW_TAGS,
        deny_high_risk=True,
        # 第一期只读：写能力在**裁剪阶段**就不进模型视野。
        # Policy 的写闸是第二道（拦截），两道都要有——只裁剪防不住幻觉 id，
        # 只拦截则会把写能力暴露给模型（信息泄露 + 选择困难）。
        deny_write=True,
        # env 门控写放行（默认空=零 diff）：只豁免 deny_write 一层，
        # deny_high_risk 永不豁免（判序在其前）。
        allow_write_tags_any=_allow_write_tags_from_env(),
    )
