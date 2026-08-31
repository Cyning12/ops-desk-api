"""Model catalog and fallback chains."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Model metadata."""

    id: str
    name: str
    test_only: bool = False


# SiliconFlow 默认列表兜底（SILICONFLOW_MODELS 未设/非法时使用）；首项 = 默认模型
_DEFAULT_SILICONFLOW_MODELS: list[ModelInfo] = [
    ModelInfo(id="deepseek-ai/DeepSeek-V4-Flash", name="DeepSeek V4 Flash"),
    ModelInfo(id="deepseek-ai/DeepSeek-V4-Pro", name="DeepSeek V4 Pro"),
    ModelInfo(id="Qwen/Qwen3.6-27B", name="Qwen3.6 27B"),
]

# 兼容旧名：测试/文档仍可能引用；运行时以 resolve_siliconflow_models() 为准
SILICONFLOW_MODELS = _DEFAULT_SILICONFLOW_MODELS

BAILIAN_FALLBACK_CHAIN = [
    ModelInfo(id="kimi/kimi-k2.7-code", name="Kimi K2.7 Code", test_only=True),
    ModelInfo(id="ZHIPU/GLM-5.2", name="GLM-5.2", test_only=True),
    ModelInfo(id="deepseek-v4-pro", name="DeepSeek V4 Pro"),
    ModelInfo(id="deepseek-v4-flash", name="DeepSeek V4 Flash"),
    ModelInfo(id="qwen3.7-plus", name="Qwen 3.7 Plus"),
]


def _display_name_from_id(model_id: str) -> str:
    """从 model id 推导展示名（取最后一段）。"""
    return model_id.rsplit("/", 1)[-1]


def parse_siliconflow_models_env(raw: str | None) -> list[ModelInfo] | None:
    """解析 ``SILICONFLOW_MODELS``。

    格式：逗号分隔 model id；可选 ``id|显示名``。
    空串 / 仅空白 / 解析后无有效 id → 返回 None（调用方回退默认列表）。
    """
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None

    models: list[ModelInfo] = []
    for part in text.split(","):
        token = part.strip()
        if not token:
            continue
        if "|" in token:
            model_id, _, name = token.partition("|")
            model_id = model_id.strip()
            name = name.strip() or _display_name_from_id(model_id)
        else:
            model_id = token
            name = _display_name_from_id(model_id)
        if not model_id:
            continue
        models.append(ModelInfo(id=model_id, name=name))
    return models or None


def resolve_siliconflow_models() -> list[ModelInfo]:
    """env 列表优先；否则代码默认列表。"""
    parsed = parse_siliconflow_models_env(os.getenv("SILICONFLOW_MODELS"))
    if parsed is None:
        return list(_DEFAULT_SILICONFLOW_MODELS)
    return parsed


def get_models_for_provider(provider: str) -> list[dict]:
    """Return available models for a provider, including fallback chain metadata."""
    if provider == "siliconflow":
        return [{"id": m.id, "name": m.name} for m in resolve_siliconflow_models()]
    if provider == "bailian":
        return [
            {"id": m.id, "name": m.name, "test_only": m.test_only}
            for m in BAILIAN_FALLBACK_CHAIN
        ]
    raise ValueError(f"Unknown provider: {provider}")


def get_default_model(provider: str) -> str:
    """Return default model for provider（siliconflow = 解析后列表首项）。"""
    if provider == "siliconflow":
        return resolve_siliconflow_models()[0].id
    if provider == "bailian":
        return "deepseek-v4-pro"
    raise ValueError(f"Unknown provider: {provider}")


def get_fallback_chain(provider: str) -> list[ModelInfo]:
    """Return fallback chain for provider."""
    if provider == "bailian":
        return BAILIAN_FALLBACK_CHAIN
    return []
