"""Prompt 装配层：模板 registry + render API。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.ops.prompts.templates import TEMPLATES


@dataclass(frozen=True)
class PromptTemplate:
    """命名模板（含 version）。"""

    template_id: str
    version: str
    body: str


class PromptTemplateNotFoundError(KeyError):
    """未知 template_id。"""


def get_template(template_id: str) -> PromptTemplate:
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
        text = tmpl.body.format(**vars_map)
    except KeyError as exc:
        raise KeyError(f"模板 {template_id} 缺少变量: {exc}") from exc
    if slots:
        for name, content in slots.items():
            block = (content or "").strip()
            if block:
                text = f"{text}\n\n<!-- slot:{name} -->\n{block}"
    return text
