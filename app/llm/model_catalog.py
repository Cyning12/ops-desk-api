"""Model catalog and fallback chains."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

_logger = logging.getLogger(__name__)


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


# --- 任务类型分层路由（llm-layer-hardening D3） ---
#
# 解析序（钉死）：显式 model= > env 档覆盖 OPS_LLM_TIER_<TASK>_MODEL > 档默认
# > settings.ops_llm_model（由调用方兜底，本函数返回 None 表示「本层无意见，
# 沿用现网默认」）。非法档（空/不在已知目录）/未知 task → 回退默认 + warning，
# 不炸请求。grader 档并入既有 RAG_GRADER_MODEL 覆盖链（不破坏现网配置）。

TASK_TYPES: tuple[str, ...] = ("answer", "grader", "extract", "structured", "summary")

#: 档默认表：None = 不落档（回退 settings.ops_llm_model / provider 默认）。
#: grader 档默认 = 现网 RAG_GRADER_MODEL 未设时的取值（契约 4b 便宜模型）。
TASK_TIER_MODELS: dict[str, str | None] = {
    "answer": None,
    "grader": "Qwen/Qwen3.6-27B",
    "extract": None,
    "structured": None,
    # session-summary-fallback（T2 新增 summary 档）：会话摘要与 extract 延迟预算
    # 不同（懒生成在请求路径 · extract 是 background 面），独立档独立调档；
    # 默认 None = 不落档沿用现网默认（灰度期 OPS_LLM_TIER_SUMMARY_MODEL 调档零改码）
    "summary": None,
}


def _known_model_ids() -> set[str]:
    """已知模型目录（siliconflow 解析列表 ∪ bailian 链）；env 档校验用。

    目录可经 SILICONFLOW_MODELS 扩展——自定义模型先入目录再入档。
    """
    ids = {m.id for m in resolve_siliconflow_models()}
    ids |= {m.id for m in BAILIAN_FALLBACK_CHAIN}
    return ids


def resolve_task_model(
    task_type: str, explicit_model: str | None = None
) -> tuple[str | None, str]:
    """任务类型 → 模型档解析。返回 (model 或 None, source)。

    None 表示分层路由**无意见**：调用方沿用现网默认解析（逐字节一致）。
    source ∈ explicit / env_tier / rag_grader_model / tier_default / default /
    unknown_task（观测：写 span metadata 与 usage 行 task_type 的依据）。
    """
    if explicit_model and explicit_model.strip():
        return explicit_model.strip(), "explicit"
    task = (task_type or "").strip().lower()
    if task not in TASK_TIER_MODELS:
        _logger.warning(
            "unknown llm task_type=%r; fallback to default model resolution", task_type
        )
        return None, "unknown_task"

    env_name = f"OPS_LLM_TIER_{task.upper()}_MODEL"
    raw = (os.getenv(env_name) or "").strip()
    if raw:
        if raw in _known_model_ids():
            return raw, "env_tier"
        _logger.warning("%s=%r 不在已知模型目录；回退档默认", env_name, raw)
    if task == "grader":
        # 兼容现网：RAG_GRADER_MODEL 并入 grader 档覆盖链（直读不校验，
        # 与改前 rag_nodes.GRADER_MODEL 语义一致）
        legacy = (os.getenv("RAG_GRADER_MODEL") or "").strip()
        if legacy:
            return legacy, "rag_grader_model"
    tier = TASK_TIER_MODELS[task]
    if tier:
        return tier, "tier_default"
    return None, "default"
