"""写入闸（纯函数 · 无 DB · 无 IO）：判据在写入时判，不在检索时筛。

三判据（SPEC §1 纪律）落成显式可测规则：

| 判据 | 落成规则 | 拒绝原因码 |
|------|----------|------------|
| 与主体相关 | `tenant_id` / `user_id` 均非空（事实必须绑定主体） | `missing_subject` |
| 稳定 | `key` 符合小写点分层（≥2 段，见 README 命名约定） | `invalid_key` |
| 稳定 | `key` 不以易失前缀开头（`tmp.`/`session.`/`ephemeral.`/`draft.`） | `volatile_key` |
| 可复用 | `value` 为 JSON 标量（str/int/float/bool，非 null）且非空串 | `value_not_scalar` / `empty_value` |
| 可复用 | `value` 序列化长度 ≤ `MEMORY_FACTS_MAX_VALUE_CHARS`（默认 2000） | `value_too_large` |
| 类型 | `kind` ∈ `ALLOWED_KINDS`（fact / preference） | `kind_not_allowed` |
| 域绑定 | `kind=preference` ⟺ key 首段 == `pref`（双向） | `key_kind_mismatch` |

**拒绝 = 不落库**（不是"存了不召回"）；原因码稳定可枚举，调用方按码断言。

显式-only（memory-preference-profile）：闸是纯函数不感知来源；preference
仅经显式 service API 通路构造，抽取管道产物永远 kind=fact（extract.py
schema 无 kind 字段 + 构造点钉死）——推断型偏好首期**无写入通路**。
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

KIND_FACT = "fact"
KIND_PREFERENCE = "preference"
#: 放开的 kind 集合（memory-preference-profile：preference 首期只收显式声明）
ALLOWED_KINDS = frozenset({KIND_FACT, KIND_PREFERENCE})
DEFAULT_MAX_VALUE_CHARS = 2000

# 拒绝原因码（稳定可枚举；测试与调用方按码断言，不按文案）
REASON_KIND_NOT_ALLOWED = "kind_not_allowed"
REASON_KEY_KIND_MISMATCH = "key_kind_mismatch"
REASON_INVALID_KEY = "invalid_key"
REASON_VOLATILE_KEY = "volatile_key"
REASON_MISSING_SUBJECT = "missing_subject"
REASON_VALUE_NOT_SCALAR = "value_not_scalar"
REASON_EMPTY_VALUE = "empty_value"
REASON_VALUE_TOO_LARGE = "value_too_large"

REJECT_REASONS = frozenset(
    {
        REASON_KIND_NOT_ALLOWED,
        REASON_KEY_KIND_MISMATCH,
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
    """写入闸候选：由 service API 显式构造；LLM 抽取管道产物永远 kind=fact。

    preference 首期**只收显式声明**（memory-preference-profile 显式-only）：
    闸不感知来源，显式-only 由写入通路保证（extract.py schema 无 kind 字段
    + 构造点钉死 kind=fact），推断型偏好无写入通路。
    """

    tenant_id: str
    user_id: str
    key: str
    value: Any
    kind: str = KIND_FACT


@dataclass(frozen=True)
class Decision:
    """闸判定：`allowed` + 拒绝 `reason_code`（放行时为空串）。"""

    allowed: bool
    reason_code: str = ""


def should_write(candidate: FactCandidate, *, max_chars: int | None = None) -> Decision:
    """写入闸纯函数：任一规则不过即拒，**调用方不得落库**。"""
    # 类型：kind 必须在放开集合内（集合外如 "profile" → 拒）
    if candidate.kind not in ALLOWED_KINDS:
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
    # 双向 key 域绑定：preference ⟺ key 首段 == pref（跨 kind 不互相
    # supersede 的第一道防线；第二道在 service supersede 谓词含 kind）
    if (candidate.kind == KIND_PREFERENCE) != (key.split(".", 1)[0] == "pref"):
        return Decision(False, REASON_KEY_KIND_MISMATCH)
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
