"""Prompt 模板 registry（真值已迁 ``assets/*.md`` · task prompt-asset-roadmap-p1）。

``TEMPLATES`` 由加载器喂：键集合 = 资产白名单（11 模板），value 含
``version`` / ``body``；``get_template()`` / ``render()`` 对外语义不变。

P4-T2 域机制（19 契约 §3.2）：白名单编译期不动；``TEMPLATES`` 保持构建
ops 默认面（import 期零 diff · 不建 assets/ops/）；``get_template_for_domain()``
为域化薄封装（域件命中用域件 · 缺失回退根目录 · §3.1）。
"""

from __future__ import annotations

from app.ops.prompts.loader import load_asset

_TEMPLATE_IDS = (
    "lg_rag.intent.system",
    "lg_rag.supervisor.system",
    "lg_rag.supervisor.suffix.system",
    "lg_rag.router.system",
    "lg_rag.direct.system",
    "lg_rag.rewrite.system",
    "lg_rag.extract.system",
    "lg_rag.aggregator.system",
    "memory.extract.system",
    "session.summary.system",
    # query-coref-rewrite D2：指代消解重写器（无变量 · 历史经 user 消息传入）
    "lg_rag.query_rewrite.system",
)

TEMPLATES: dict[str, dict[str, str]] = {
    template_id: {"version": version, "body": body}
    for template_id in _TEMPLATE_IDS
    for version, body in [load_asset(template_id)]
}


def get_template_for_domain(template_id: str, domain: str) -> dict[str, str]:
    """域化薄封装（19 §3.2）：白名单内模板按域目录回退加载（§3.1）。

    白名单外 id → KeyError（与 TEMPLATES 查键同语义）；``TEMPLATES`` 构建
    保持 ops 默认面不委托本函数（import 期零 diff · §3.4 不建 assets/ops/）。
    """
    if template_id not in _TEMPLATE_IDS:
        raise KeyError(template_id)
    version, body = load_asset(template_id, domain)
    return {"version": version, "body": body}
