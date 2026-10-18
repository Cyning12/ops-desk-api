"""LLM Provider factory."""

from app.config import settings
from app.llm.providers.bailian import BailianProvider
from app.llm.providers.base import BaseProvider
from app.llm.providers.siliconflow import SiliconFlowProvider

_PROVIDERS: dict[str, type[BaseProvider]] = {
    "siliconflow": SiliconFlowProvider,
    "bailian": BailianProvider,
}


def get_llm_provider(provider_name: str | None = None) -> BaseProvider:
    """Return configured LLM provider instance."""
    name = (provider_name or settings.ops_llm_provider).lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown LLM provider: {name}")
    return cls()
