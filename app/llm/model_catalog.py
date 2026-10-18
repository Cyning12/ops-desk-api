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
            {"id": m.id, "name": m.name, "test_only": m.test_only} for m in BAILIAN_FALLBACK_CHAIN
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
# 解析序（钉死 · V1-E 增策略包层）：显式 model= > env 档覆盖
# OPS_LLM_TIER_<TASK>_MODEL > 策略包（OPS_LLM_STRATEGY_PACK）> 档默认
# > settings.ops_llm_model（由调用方兜底，本函数返回 None 表示「本层无意见，
# 沿用现网默认」）。非法档（空/不在已知目录）/未知 task → 回退默认 + warning，
# 不炸请求。grader 档并入既有 RAG_GRADER_MODEL 覆盖链（不破坏现网配置）。
# 策略包缺省未设 = 现状逐字节（不读 YAML）。

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


def resolve_task_model(task_type: str, explicit_model: str | None = None) -> tuple[str | None, str]:
    """任务类型 → 模型档解析。返回 (model 或 None, source)。

    None 表示分层路由**无意见**：调用方沿用现网默认解析（逐字节一致）。
    source ∈ explicit / env_tier / rag_grader_model / strategy_pack /
    tier_default / default / unknown_task（观测：写 span metadata 与 usage
    行 task_type 的依据）。
    """
    if explicit_model and explicit_model.strip():
        return explicit_model.strip(), "explicit"
    task = (task_type or "").strip().lower()
    if task not in TASK_TIER_MODELS:
        _logger.warning("unknown llm task_type=%r; fallback to default model resolution", task_type)
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
    # 策略包层（V1-E）：仅当 OPS_LLM_STRATEGY_PACK 设置且声明该档时覆盖代码默认
    from app.llm.strategy_pack import _MISSING, pack_tier_model

    pack_val = pack_tier_model(task)
    if pack_val is not _MISSING:
        if pack_val is None:
            return None, "strategy_pack"
        model = str(pack_val).strip()
        if model in _known_model_ids():
            return model, "strategy_pack"
        _logger.warning("strategy_pack tier %s=%r 不在已知模型目录；回退代码默认", task, model)
    tier = TASK_TIER_MODELS[task]
    if tier:
        return tier, "tier_default"
    return None, "default"


# --- 档级 fallback 链声明（host-v1-llm-factory-closure D4 · 声明式降级） ---
#
# 纪律（SPEC §2 D4 锁死）：
# - **集中不散落**：降级链只在这里声明；调用点（providers/base.py 预算闸）
#   只问 catalog 要链，**禁止在调用点写死降级模型**（D6 grep 守护断言）。
# - **声明才降级**（防假降级 U3 承 capability/fallback B1-B4）：无声明档 =
#   明确失败（承 ACTION_NONE 默认），框架绝不猜降级目标。
# - 链元素两类：① 已知目录内 model id（小模型档）；② 规则档标记
#   ``rule:<name>``（Q3 裁定：固定文案模板档，文案见 RULE_TIER_TEMPLATES）。
# - 链序 = 预算耗尽 → 小模型档 → 规则/缓存档；链长 ≤ 3 且无环（承 B3，FP-8）。

#: 规则档标记前缀（``rule:<name>`` · name 须在 RULE_TIER_TEMPLATES 词表内）
RULE_TIER_PREFIX = "rule:"

#: 规则档词表（Q3 固定文案模板档 · 零逻辑）：name → 静态兜底文案。
#: 词表即声明面：新增规则档 = 在此登记文案（走 Git + PR + 人闸）。
RULE_TIER_TEMPLATES: dict[str, str] = {
    "static_refusal": (
        "当前服务负载/预算已触上限，暂时无法完成本次回答。"
        "请稍后重试；若持续出现请联系管理员调整额度。"
    ),
}

#: 档级 fallback 链：task_type → (降级目标, ...)，大 → 小 → ``rule:<name>``。
#: **空 tuple = 无声明 = 预算耗尽时明确失败**（承 fallback ACTION_NONE 默认 ·
#: 业务档位是否配降级链由本声明显式决定，框架不猜）。
TASK_TIER_FALLBACKS: dict[str, tuple[str, ...]] = {
    # answer 是终答面：耗尽先退小模型档，再退固定文案（标记 degraded 跟数据走）
    "answer": ("deepseek-ai/DeepSeek-V4-Flash", "rule:static_refusal"),
    # 背景档无声明：grader/extract/structured/summary 耗尽 = 明确失败
    "grader": (),
    "extract": (),
    "structured": (),
    "summary": (),
}

#: 降级链长度上限（承 capability/fallback B3 链条有界 · SPEC FP-8）
FALLBACK_CHAIN_MAX_LEN = 3


def resolve_fallback_chain(task_type: str) -> tuple[str, ...]:
    """任务类型 → 校验后的降级链（纯函数 · 非法档过滤 + warning，不炸请求）。

    校验（承 :157-167 回退纪律 · SPEC FP-8）：
    - 未知 task_type → warning + 空链（= 明确失败，不静默放行）；
    - 非法元素（不在已知模型目录、且非词表内 ``rule:<name>``）→ warning + 过滤；
    - 去环：链内重复元素只保留首次出现（warning）；
    - 链长截断到 FALLBACK_CHAIN_MAX_LEN（warning）。
    """
    task = (task_type or "").strip().lower()
    if task not in TASK_TYPES:
        _logger.warning(
            "unknown llm task_type=%r; fallback chain empty (explicit failure)", task_type
        )
        return ()
    from app.llm.strategy_pack import pack_tier_fallbacks

    pack_fb = pack_tier_fallbacks(task)
    declared = pack_fb if pack_fb is not None else (TASK_TIER_FALLBACKS.get(task) or ())
    known_ids = _known_model_ids()
    chain: list[str] = []
    seen: set[str] = set()
    for entry in declared:
        item = (entry or "").strip()
        if not item:
            continue
        if item in seen:
            _logger.warning("fallback chain task=%s 含重复元素 %r（成环风险）· 已去重", task, item)
            continue
        if item.startswith(RULE_TIER_PREFIX):
            rule_name = item[len(RULE_TIER_PREFIX) :]
            if rule_name not in RULE_TIER_TEMPLATES:
                _logger.warning(
                    "fallback chain task=%s 规则档 %r 不在 RULE_TIER_TEMPLATES 词表 · 已过滤",
                    task,
                    item,
                )
                continue
        elif item not in known_ids:
            _logger.warning("fallback chain task=%s 元素 %r 不在已知模型目录 · 已过滤", task, item)
            continue
        seen.add(item)
        chain.append(item)
        if len(chain) >= FALLBACK_CHAIN_MAX_LEN:
            if len(declared) > FALLBACK_CHAIN_MAX_LEN:
                _logger.warning(
                    "fallback chain task=%s 超过链长上限 %d · 已截断",
                    task,
                    FALLBACK_CHAIN_MAX_LEN,
                )
            break
    return tuple(chain)


def rule_tier_text(name: str) -> str | None:
    """规则档静态文案；未声明 → None（链末端明确失败 · 不伪造成功）。"""
    return RULE_TIER_TEMPLATES.get((name or "").strip())


# --- 档级单价表（host-v1-llm-factory-closure D4/D5 · 估算口径 · 非对账） ---
#
# 纪律（SPEC §2 D5 / FP-7 锁死）：
# - **仅估算口径**：单位「元/1K tokens」，用于 Cost per Successful Task 估算与
#   span 观测，**不是计费对账**（跨 provider 对账是 v2.0 非范围）。
# - 缺单价档 → estimate_cost 返回 None → 聚合标 ``unknown``，**不伪造 0**
#   （承「不写 0 假账」铁律）。

#: model id → {"input": 元/1K input tokens, "output": 元/1K output tokens}
MODEL_UNIT_PRICES: dict[str, dict[str, float]] = {
    "deepseek-ai/DeepSeek-V4-Flash": {"input": 0.001, "output": 0.002},
    "deepseek-ai/DeepSeek-V4-Pro": {"input": 0.004, "output": 0.008},
    "Qwen/Qwen3.6-27B": {"input": 0.002, "output": 0.004},
}


def estimate_cost(model: str | None, prompt_tokens: int, completion_tokens: int) -> float | None:
    """按档级单价表估算本次调用成本（元）；缺单价 → None（unknown 不伪造 0）。

    单价解析：策略包 ``model_unit_prices``（若已加载且声明）> 代码
    ``MODEL_UNIT_PRICES``。
    """
    mid = (model or "").strip()
    from app.llm.strategy_pack import pack_unit_price

    price = pack_unit_price(mid) or MODEL_UNIT_PRICES.get(mid)
    if price is None:
        return None
    return (
        max(0, int(prompt_tokens)) / 1000.0 * price["input"]
        + max(0, int(completion_tokens)) / 1000.0 * price["output"]
    )
