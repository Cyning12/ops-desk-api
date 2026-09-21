"""Prompt 模板 registry（真值已迁 ``assets/*.md`` · task prompt-asset-roadmap-p1）。

``TEMPLATES`` 由加载器喂：键集合 = 资产白名单（10 模板），value 含
``version`` / ``body``；``get_template()`` / ``render()`` 对外语义不变。
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
)

TEMPLATES: dict[str, dict[str, str]] = {
    template_id: {"version": version, "body": body}
    for template_id in _TEMPLATE_IDS
    for version, body in [load_asset(template_id)]
}
