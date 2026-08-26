"""complete_structured：LLM → parse_only → 预算内 OUTPUT CORRECTION 重试。

``max_retries`` 语义（与单测一致）：
- ``max_retries`` = 失败后允许的**重试次数**（再请求次数）
- **总尝试次数 = max_retries + 1**（含首次）
- 默认 ``max_retries=3`` → 最多 4 次 ``provider.complete``
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.llm.factory import get_llm_provider
from app.llm.schema import BaseProvider, LlmMessage
from app.ops.structured_output.parse import parse_only

T = TypeVar("T", bound=BaseModel)

DEFAULT_MAX_RETRIES = 3
_CORRECTION_MARKER = "OUTPUT CORRECTION"
# 字段级 / 整段校验 reason 截断上限，避免 correction 泄漏过长原文
_CORRECTION_REASON_MAX = 400


@dataclass(frozen=True)
class LlmCtx:
    """可选覆盖：provider 名（走 get_llm_provider）与 model。"""

    provider: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class StructuredFailure(Generic[T]):
    """预算耗尽或不可重试失败。Host 权威：不携带成功业务 data。"""

    error: str
    attempts: int
    last_raw: str | None = None
    no_retry: bool = False


class StructuredOutputError(Exception):
    """``raise_on_failure=True`` 时包装 ``StructuredFailure`` 上抛。"""

    def __init__(self, failure: StructuredFailure[Any]) -> None:
        super().__init__(failure.error)
        self.failure = failure


def _truncate_reason(reason: str, *, limit: int = _CORRECTION_REASON_MAX) -> str:
    text = (reason or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _build_correction_user_content(error: str) -> str:
    """注入 OUTPUT CORRECTION；字段级 reason 截断。完整重生成，非半截补丁。"""
    truncated = _truncate_reason(error)
    return (
        f"{_CORRECTION_MARKER}\n"
        "Previous output failed host validation. "
        "Regenerate the COMPLETE JSON object "
        "(full regeneration; do not patch only failed fields).\n"
        f"Validation reason (truncated): {truncated}"
    )


def _normalize_messages(
    messages: Sequence[LlmMessage] | None,
    *,
    system: str | None,
    user: str | None,
) -> list[LlmMessage]:
    if messages is not None:
        return [LlmMessage(role=m.role, content=m.content) for m in messages]
    if system is None or user is None:
        raise ValueError("Provide messages=... or both system= and user=")
    return [
        LlmMessage(role="system", content=system),
        LlmMessage(role="user", content=user),
    ]


def _resolve_provider(
    llm_ctx: LlmCtx | None,
    *,
    provider_override: BaseProvider | None,
) -> tuple[BaseProvider, str | None]:
    if provider_override is not None:
        model = llm_ctx.model if llm_ctx else None
        return provider_override, model
    ctx = llm_ctx or LlmCtx()
    return get_llm_provider(ctx.provider), ctx.model


async def acomplete_structured(
    messages: Sequence[LlmMessage] | None = None,
    *,
    system: str | None = None,
    user: str | None = None,
    schema: type[T],
    ensure_keys: Sequence[str] | None = None,
    validate: Callable[[T], str | None] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    raise_on_failure: bool = True,
    llm_ctx: LlmCtx | None = None,
    no_retry: bool = False,
    _provider: BaseProvider | None = None,
) -> T | StructuredFailure[T]:
    """触发 LLM 并走 parse_only；失败则预算内注入 OUTPUT CORRECTION 后完整重生成。

    ``ensure_keys``：点分必填路径（见 ``parse._walk_dot_path`` 约定）；缺/null → Host 失败。
    ``validate``：自定义 callable，返回失败 reason 字符串或 ``None``（通过）。
    失败 reason 进入 OUTPUT CORRECTION（完整重生成）；``no_retry=True`` 时**不**注入
    correction、不重试——敏感规则 fail-closed，避免泄漏进 prompt。

    ``_provider``：仅供单测注入 mock；生产路径用 ``llm_ctx`` + ``get_llm_provider``。
    """
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")

    # 总尝试次数 = max_retries + 1（见模块注释）
    max_attempts = max_retries + 1
    working = _normalize_messages(messages, system=system, user=user)
    provider, model = _resolve_provider(llm_ctx, provider_override=_provider)

    last_error = "structured output failed"
    last_raw: str | None = None
    attempts_done = 0

    for attempt in range(max_attempts):
        raw = await provider.complete(working, model=model)
        attempts_done = attempt + 1
        last_raw = raw
        outcome = parse_only(
            raw,
            schema=schema,
            ensure_keys=ensure_keys,
            validate=validate,
        )
        if outcome.ok and outcome.data is not None:
            return outcome.data

        last_error = outcome.error or "validation failed"

        # 敏感规则：不把隐藏规则 / reason 写入 correction，直接失败
        if no_retry:
            break

        # 预算内：注入 correction，进入下一次完整重生成
        if attempt + 1 >= max_attempts:
            break
        correction = _build_correction_user_content(last_error)
        working = [
            *working,
            LlmMessage(role="assistant", content=raw),
            LlmMessage(role="user", content=correction),
        ]

    failure: StructuredFailure[T] = StructuredFailure(
        error=last_error,
        attempts=attempts_done,
        last_raw=last_raw,
        no_retry=no_retry,
    )
    if raise_on_failure:
        raise StructuredOutputError(failure)
    return failure


# SPEC 表面名；实现为 async，对齐 provider.complete
complete_structured = acomplete_structured
