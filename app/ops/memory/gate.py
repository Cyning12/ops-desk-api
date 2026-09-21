"""写入闸（纯函数 · 无 DB · 无 IO）：判据在写入时判，不在检索时筛。

三判据（SPEC §1 纪律）落成显式可测规则：

| 判据 | 落成规则 | 拒绝原因码 |
|------|----------|------------|
| 与主体相关 | `tenant_id` / `user_id` 均非空（事实必须绑定主体） | `missing_subject` |
| 稳定 | `key` 符合小写点分层（≥2 段，见 README 命名约定） | `invalid_key` |
| 稳定 | `key` 不以易失前缀开头（`tmp.`/`session.`/`ephemeral.`/`draft.`） | `volatile_key` |
| 可复用 | `value` 为 JSON 标量（str/int/float/bool，非 null）且非空串 | `value_not_scalar` / `empty_value` |
| 可复用 | `value` 序列化长度 ≤ `MEMORY_FACTS_MAX_VALUE_CHARS`（默认 2000） | `value_too_large` |
| 类型 | `kind` 仅接受 `fact`（preference 属画像，P1+） | `kind_not_allowed` |

**拒绝 = 不落库**（不是"存了不召回"）；原因码稳定可枚举，调用方按码断言。
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

ALLOWED_KIND = "fact"
DEFAULT_MAX_VALUE_CHARS = 2000

# 拒绝原因码（稳定可枚举；测试与调用方按码断言，不按文案）
REASON_KIND_NOT_ALLOWED = "kind_not_allowed"
REASON_INVALID_KEY = "invalid_key"
REASON_VOLATILE_KEY = "volatile_key"
REASON_MISSING_SUBJECT = "missing_subject"
REASON_VALUE_NOT_SCALAR = "value_not_scalar"
REASON_EMPTY_VALUE = "empty_value"
REASON_VALUE_TOO_LARGE = "value_too_large"

REJECT_REASONS = frozenset(
    {
        REASON_KIND_NOT_ALLOWED,
        REASON_INVALID_KEY,
        REASON_VOLATILE_KEY,
        REASON_MISSING_SUBJECT,
        REASON_VALUE_NOT_SCALAR,
        REASON_EMPTY_VALUE,
        REASON_VALUE_TOO_LARGE,
    }
)

# key 命名约定：小写点分层，至少两段（域.名），如 `project.primary_repo`
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
# 易失前缀：这类 key 承载的是一次性上下文，不是稳定事实
_VOLATILE_PREFIXES = ("tmp.", "session.", "ephemeral.", "draft.")


def max_value_chars() -> int:
    """`MEMORY_FACTS_MAX_VALUE_CHARS`；非法或 ≤0 → 默认 2000 + warning。"""
    raw = (os.getenv("MEMORY_FACTS_MAX_VALUE_CHARS") or "").strip()
    if not raw:
        return DEFAULT_MAX_VALUE_CHARS
    try:
        n = int(raw)
    except ValueError:
        logger.warning(
            "invalid MEMORY_FACTS_MAX_VALUE_CHARS=%r; fallback to %d",
            raw,
            DEFAULT_MAX_VALUE_CHARS,
        )
        return DEFAULT_MAX_VALUE_CHARS
    if n <= 0:
        logger.warning(
            "MEMORY_FACTS_MAX_VALUE_CHARS=%r <= 0; fallback to %d",
            raw,
            DEFAULT_MAX_VALUE_CHARS,
        )
        return DEFAULT_MAX_VALUE_CHARS
    return n


@dataclass(frozen=True)
class FactCandidate:
    """写入闸候选：P0 仅由 service API 显式构造（LLM 自动抽取是 P1）。"""

    tenant_id: str
    user_id: str
    key: str
    value: Any
    kind: str = ALLOWED_KIND


@dataclass(frozen=True)
class Decision:
    """闸判定：`allowed` + 拒绝 `reason_code`（放行时为空串）。"""

    allowed: bool
    reason_code: str = ""


def should_write(candidate: FactCandidate, *, max_chars: int | None = None) -> Decision:
    """写入闸纯函数：任一规则不过即拒，**调用方不得落库**。"""
    # 类型：P0 只接受事实
    if candidate.kind != ALLOWED_KIND:
        return Decision(False, REASON_KIND_NOT_ALLOWED)
    # 与主体相关：事实必须绑定 (tenant, user)
    if not (candidate.tenant_id or "").strip() or not (candidate.user_id or "").strip():
        return Decision(False, REASON_MISSING_SUBJECT)
    # 稳定：key 小写点分层 ≥2 段，且非易失前缀
    key = (candidate.key or "").strip()
    if not _KEY_RE.match(key):
        return Decision(False, REASON_INVALID_KEY)
    if key.startswith(_VOLATILE_PREFIXES):
        return Decision(False, REASON_VOLATILE_KEY)
    # 可复用：原子标量事实，拒绝复合快照 / 空值
    value = candidate.value
    if isinstance(value, bool):
        pass  # bool 是 int 子类，先判
    elif isinstance(value, (int, float)):
        pass
    elif isinstance(value, str):
        if not value.strip():
            return Decision(False, REASON_EMPTY_VALUE)
    else:
        return Decision(False, REASON_VALUE_NOT_SCALAR)
    limit = max_chars if max_chars is not None else max_value_chars()
    if len(json.dumps(value, ensure_ascii=False)) > limit:
        return Decision(False, REASON_VALUE_TOO_LARGE)
    return Decision(True)
