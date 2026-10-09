"""Strategy Builder 候选 capability allowlist 配置（规则 · 无 LLM）。

生产默认：按 ``agent_type`` / ``mode`` 查显式 map；**禁止** ``None``=全开。
未知 key → 空列表（fail-closed）。测试可 patch ``CANDIDATE_CAPABILITY_IDS``
为显式 list 覆盖 map。

运维 env 追加口 ``OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS``（逗号分隔 ·
逐项 strip · 去空 · 保序去重）：在 map 解析结果（含未知 key 空列表）之后
追加显式候选集；**默认不设 = 解析结果与不设时逐字节零 diff**。env 只抬
候选层，下游 ∩visible / deny 判序 / Policy 写闸全链不动（候选 ≠ 放行）。
覆盖口 ``CANDIDATE_CAPABILITY_IDS`` 生效时**不追加** env（测试钩子纯净）。
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# 最小只读集（未知 key 不走此集；未知 → []）
MINIMAL_READONLY_CAPABILITY_IDS: list[str] = ["utc_now_iso"]

# agent_type / mode → 显式 allowlist（supervisor 图默认走 "supervisor"）
CAPABILITY_ALLOWLIST_BY_KEY: dict[str, list[str]] = {
    "supervisor": [
        "utc_now_iso",
        "mock_get_issue_status",
        "mock_get_deploy_info",
        "get_issue_by_number",
        "get_pr_by_number",
    ],
    "default": list(MINIMAL_READONLY_CAPABILITY_IDS),
}

# 测试/运维显式覆盖：非 None 时优先于 map（须为 list；禁止用 None 表示全开）
CANDIDATE_CAPABILITY_IDS: list[str] | None = None

# 运维 env 追加口：逗号分隔候选 id（map 解析结果之后追加 · 含未知 key）
EXTRA_CANDIDATE_CAPABILITY_IDS_ENV = "OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS"


def _extra_candidate_capability_ids() -> list[str]:
    """读 env 追加集：逐项 strip · 去空 · 保序去重；未设 / 全空白 → ``[]``。

    **调用点读取**（函数内读 ``os.environ`` · 禁模块 import 时固化）：
    builder 节点每轮调用本函数，测试内 monkeypatch 直接生效。
    """
    raw = os.environ.get(EXTRA_CANDIDATE_CAPABILITY_IDS_ENV, "")
    if not raw.strip():
        return []
    seen: set[str] = set()
    extra: list[str] = []
    for part in raw.split(","):
        item = part.strip()
        if item and item not in seen:
            seen.add(item)
            extra.append(item)
    return extra


def get_candidate_capability_ids(
    *,
    agent_type: str | None = None,
    mode: str | None = None,
) -> list[str]:
    """解析本轮候选 id；永不返回 ``None``（全开已废弃）。

    优先级：显式 ``CANDIDATE_CAPABILITY_IDS`` list → map[agent_type|mode] →
    未知 key 空列表。env 追加集（``OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS``）
    在 map 解析结果（含未知 key 空列表）之后追加；覆盖口生效时**不追加**。
    """
    if CANDIDATE_CAPABILITY_IDS is not None:
        return list(CANDIDATE_CAPABILITY_IDS)
    key = (agent_type or mode or "supervisor").strip().lower() or "supervisor"
    mapped = CAPABILITY_ALLOWLIST_BY_KEY.get(key)
    candidates = list(mapped) if mapped is not None else []
    extra = _extra_candidate_capability_ids()
    if extra:
        logger.info(
            "strategy 候选 env 追加集生效：count=%d ids=%s",
            len(extra),
            extra,
        )
        candidates.extend(extra)
    return candidates
