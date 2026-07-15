"""Model catalog and fallback chains."""
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Model metadata."""

    id: str
    name: str
    test_only: bool = False


SILICONFLOW_MODELS = [
    ModelInfo(id="deepseek-ai/DeepSeek-V4-Pro", name="DeepSeek V4 Pro"),
    ModelInfo(id="Qwen/Qwen2.5-72B-Instruct", name="Qwen2.5 72B"),
]

BAILIAN_FALLBACK_CHAIN = [
    ModelInfo(id="kimi/kimi-k2.7-code", name="Kimi K2.7 Code", test_only=True),
    ModelInfo(id="ZHIPU/GLM-5.2", name="GLM-5.2", test_only=True),
    ModelInfo(id="deepseek-v4-pro", name="DeepSeek V4 Pro"),
    ModelInfo(id="deepseek-v4-flash", name="DeepSeek V4 Flash"),
    ModelInfo(id="qwen3.7-plus", name="Qwen 3.7 Plus"),
]


def get_default_model(provider: str) -> str:
    """Return default model for provider."""
    if provider == "siliconflow":
        return "deepseek-ai/DeepSeek-V4-Pro"
    if provider == "bailian":
        return "deepseek-v4-pro"
    raise ValueError(f"Unknown provider: {provider}")


def get_fallback_chain(provider: str) -> list[ModelInfo]:
    """Return fallback chain for provider."""
    if provider == "bailian":
        return BAILIAN_FALLBACK_CHAIN
    return []
