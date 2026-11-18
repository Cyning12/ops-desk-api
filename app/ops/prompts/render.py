"""Prompt 装配层：模板 registry + render API。"""

from __future__ import annotations

from dataclasses import dataclass
from string import Template
from typing import Any

from app.ops.prompts.domain_context import DEFAULT_DOMAIN, current_domain
from app.ops.prompts.templates import TEMPLATES, get_template_for_domain


@dataclass(frozen=True)
class PromptTemplate:
    """命名模板（含 version）。"""

    template_id: str
    version: str
    body: str


class PromptTemplateNotFoundError(KeyError):
    """未知 template_id。"""


def get_template(template_id: str) -> PromptTemplate:
    # P4-T2 域路由（19 §3.3 · 调用点零 churn）：域=ops 走 TEMPLATES 默认面
    # （现状同路径零 diff · §3.4 不建 assets/ops/）；非 ops 走域化薄封装
    # （域件命中用域件 · 缺失回退根目录 · §3.1）。
    domain = current_domain()
    raw: dict[str, str] | None
    if domain != DEFAULT_DOMAIN:
        try:
            raw = get_template_for_domain(template_id, domain)
        except KeyError:
            raise PromptTemplateNotFoundError(template_id) from None
    else:
        raw = TEMPLATES.get(template_id)
    if raw is None:
        raise PromptTemplateNotFoundError(template_id)
    return PromptTemplate(
        template_id=template_id,
        version=str(raw.get("version") or "v0"),
        body=str(raw["body"]),
    )


def render(
    template_id: str,
    variables: dict[str, Any] | None = None,
    *,
    slots: dict[str, str] | None = None,
) -> str:
    """渲染模板；``slots`` 追加在正文后（Skill provide 等注入点）。"""
    tmpl = get_template(template_id)
    vars_map = dict(variables or {})
    try:
        text = Template(tmpl.body).substitute(vars_map)
    except KeyError as exc:
        raise KeyError(f"模板 {template_id} 缺少变量: {exc}") from exc
    if slots:
        for name, content in slots.items():
            block = (content or "").strip()
            if block:
                text = f"{text}\n\n<!-- slot:{name} -->\n{block}"
    return text
