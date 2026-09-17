"""Strategy Builder 候选 capability allowlist 配置（规则 · 无 LLM）。

生产默认：按 ``agent_type`` / ``mode`` 查显式 map；**禁止** ``None``=全开。
未知 key → 空列表（fail-closed）。测试可 patch ``CANDIDATE_CAPABILITY_IDS``
为显式 list 覆盖 map。
"""

from __future__ import annotations

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


def get_candidate_capability_ids(
    *,
    agent_type: str | None = None,
    mode: str | None = None,
) -> list[str]:
    """解析本轮候选 id；永不返回 ``None``（全开已废弃）。

    优先级：显式 ``CANDIDATE_CAPABILITY_IDS`` list → map[agent_type|mode] →
    未知 key 空列表。
    """
    if CANDIDATE_CAPABILITY_IDS is not None:
        return list(CANDIDATE_CAPABILITY_IDS)
    key = (agent_type or mode or "supervisor").strip().lower() or "supervisor"
    mapped = CAPABILITY_ALLOWLIST_BY_KEY.get(key)
    if mapped is None:
        return []
    return list(mapped)
