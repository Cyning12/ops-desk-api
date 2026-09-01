"""PromptAssembly · 模板 + 变量 + slot 装配（H4）；C2 起增 Prompt Pack 层。"""

from app.ops.prompts.packs import (
    PromptPack,
    PromptPackError,
    PromptPackNotFoundError,
    render_pack,
    route_intent,
)
from app.ops.prompts.render import PromptTemplateNotFoundError, get_template, render

__all__ = [
    "PromptPack",
    "PromptPackError",
    "PromptPackNotFoundError",
    "PromptTemplateNotFoundError",
    "get_template",
    "render",
    "render_pack",
    "route_intent",
]
