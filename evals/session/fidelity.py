"""摘要保真度确定性校验（session-summary-fallback D4 · 清单=summary_fidelity_v1.yaml）。

判定面是 token 包含断言（**非语义判定 · 零 LLM-as-judge**）：
- 正向：must_keep sentinel ⊆ 摘要文本（丢关键事实 = 违规）；
- 反向：must_not_add 禁忌 sentinel 逐项不在摘要（新增幻觉 = 违规）；
- 空摘要假通过防线：空/全空白摘要直接违规（空摘要天然满足 must_not_add，
  只做反向会得到假通过）。
CI 热路径用夹具/录制摘要跑本函数；真模型离线抽检复用同一函数（evals 层纪律）。
"""
from __future__ import annotations


def check_summary_fidelity(
    summary_text: str,
    *,
    must_keep: list[str],
    must_not_add: list[str],
) -> list[str]:
    """校验候选摘要，返回违规清单（空列表 = 通过）。

    违规码形态：empty_summary / must_keep_missing:<token> /
    must_not_add_present:<token>——机器可读，人工可对账。
    """
    violations: list[str] = []
    text = summary_text or ""
    if not text.strip():
        # 空摘要假通过防线：无需继续逐项（必缺全部 must_keep）
        return ["empty_summary"]
    for token in must_keep:
        if token not in text:
            violations.append(f"must_keep_missing:{token}")
    for token in must_not_add:
        if token in text:
            violations.append(f"must_not_add_present:{token}")
    return violations
