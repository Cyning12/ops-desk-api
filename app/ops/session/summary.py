"""会话历史真摘要（session-summary-fallback · 方案 L1 懒生成 + C1 独立表缓存）。

纪律（SPEC §2/§4 钉死 · 回退铁律是上线前提）：
- **结构零改动**：轮数切分 / 条数 / 顺序 / 尾部全量轮由纯函数
  compress_window 定；本面只做占位条（[历史摘要 · N 轮 · roles=...]）
  的**内容替换**——占位 chunk → 查缓存 → miss 才调 LLM → 真摘要条。
- **任何失败 → 该 chunk 保留占位符**（LLM / 超时 / 熔断 / 资产缺失 / 缓存
  故障）：永不阻塞主答、绝不产出半摘要；span session_summary_degraded=N
  （N=降级 chunk 数）——「静默降级」与「根本没走摘要面」经标记可区分。
- **缓存 key 铁律**：sha256(prompt_version + model + chunk turns canonical
  JSON）——只用序号会在窗口滑动后命中旧摘要（缓存污染静默错）；内容变 →
  hash 变 → 自然 miss，**无主动失效逻辑**；唯一约束 (thread_id, chunk_hash)。
- **原文 SoT 零污染**：摘要只写 ops_session_summaries，绝不写
  ops_lg_rag_turns / ops_runs。
- 开关判定在装配侧（continuity.session_summary_enabled · 默认关 · off 态
  零 LLM 调用零缓存读写）；本面自身不读开关 env。
- LLM 调用走 **summary 档**（resolve_task_model("summary") · 默认 None 沿用
  现网默认 · OPS_LLM_TIER_SUMMARY_MODEL 覆盖）；usage 经 use_run_context
  （task_type="summary" · surface="lg_rag"）自动落 ops_llm_usage 归因；
  重试 / 熔断由 provider 包装层自动继承零改造。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re

from sqlalchemy import select

from app.config import settings
from app.llm.factory import get_llm_provider
from app.llm.model_catalog import resolve_task_model
from app.llm.schema import BaseProvider, LlmMessage
from app.llm.usage import use_run_context
from app.ops.prompts import get_template, render
from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

#: 摘要 prompt 资产（无变量 · chunk turns 经 user 消息传入 · memory.extract 先例）
SUMMARY_TEMPLATE_ID = "session.summary.system"
#: 单次摘要调用超时（秒 · extract.py EXTRACT_TIMEOUT_S 先例）；超时 = 该 chunk 降级占位
SUMMARY_TIMEOUT_S = 60.0
#: 摘要条有损声明锚点（模型可见「这是摘要不是原文」；锚点断言守此语义）
SUMMARY_LOSSY_NOTICE = "有损压缩，细节以最近轮为准"

#: 占位条形态锚（compress_window 产物 · 该函数零改动 · 此处只做识别不改写）
_PLACEHOLDER_RE = re.compile(r"^\[历史摘要 · (\d+) 轮 · roles=.*\]$")


def placeholder_turn_count(turn: object) -> int | None:
    """识别 compress_window 占位条，返回其轮数 N；非占位条 → None。"""
    if not isinstance(turn, dict) or turn.get("role") != "system":
        return None
    m = _PLACEHOLDER_RE.match(str(turn.get("content") or ""))
    return int(m.group(1)) if m else None


def derive_placeholder_chunks(
    source_turns: list[dict],
    *,
    max_full_turns: int,
    group_size: int,
) -> list[list[dict]] | None:
    """复现 compress_window 的占位 chunk 切分（纯推导 · 零 IO）。

    占位条按顺序 ↔ head 按 group_size 切出的 chunk 一一对应；
    切分不可复现（异常输入）→ None（调用方降级保留占位）。
    """
    try:
        turns = list(source_turns)
        if max_full_turns <= 0 or len(turns) <= max_full_turns or group_size <= 0:
            return []
        head = turns[:-max_full_turns]
        return [head[i : i + group_size] for i in range(0, len(head), group_size)]
    except Exception:
        return None


def chunk_content_hash(prompt_version: str, model: str, chunk: list[dict]) -> str:
    """缓存 key 铁律落点：sha256(prompt_version + model + chunk turns canonical JSON）。

    窗口滑动 → chunk 内容变 → hash 变 → 自然 miss（缓存污染物理防）。
    """
    canonical = json.dumps(
        {
            "prompt_version": prompt_version,
            "model": model,
            "turns": [
                {
                    "role": str(t.get("role") or "") if isinstance(t, dict) else "",
                    "content": str(t.get("content") or "") if isinstance(t, dict) else "",
                }
                for t in chunk
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def render_summary_content(
    turn_count: int, model: str, prompt_version: str, summary_text: str
) -> str:
    """真摘要条：版本 + 来源 + 有损声明三标记进上下文（锚点断言守 · 非全文快照）。"""
    header = (
        f"[历史摘要 · {prompt_version} · {turn_count} 轮 · 模型:{model} "
        f"· {SUMMARY_LOSSY_NOTICE}]"
    )
    return f"{header}\n{summary_text}"


def _render_chunk_window(chunk: list[dict]) -> str:
    """chunk turns → user 消息文本窗（prompt 资产无变量 · 分离传递先例）。"""
    lines = []
    for i, turn in enumerate(chunk, 1):
        role = str(turn.get("role") or "user") if isinstance(turn, dict) else "user"
        content = str(turn.get("content") or "") if isinstance(turn, dict) else ""
        lines.append(f"[{i}] {role}：{content}")
    return "请摘要以下早期对话轮次：\n\n" + "\n".join(lines)


def _resolve_prompt() -> tuple[str, str]:
    """读 prompt 资产，返回 (system_prompt, prompt_version)；缺失/非法显式炸。

    （loader 纪律沿用 · 调用面 try 包住 → 整体降级占位，不炸请求）
    """
    tmpl = get_template(SUMMARY_TEMPLATE_ID)
    return render(SUMMARY_TEMPLATE_ID), tmpl.version


def _resolve_model() -> tuple[str | None, str]:
    """summary 档解析：返回 (传给 provider 的 model 或 None, 标记/缓存用模型名）。

    档默认 None = 不落档沿用现网默认（settings.ops_llm_model 经 validator 恒非空）。
    """
    tier_model, _route_source = resolve_task_model("summary")
    return tier_model, tier_model or settings.ops_llm_model or ""


async def _generate_summary(
    system_prompt: str,
    chunk: list[dict],
    *,
    model: str | None,
    _provider: BaseProvider | None = None,
) -> str:
    """一次摘要 LLM 调用（summary 档 · usage ContextVar 归因继承）。

    ``_provider``：仅供单测注入 mock；生产路径走 get_llm_provider。
    """
    provider = _provider if _provider is not None else get_llm_provider()
    with use_run_context(surface="lg_rag", task_type="summary"):
        raw = await provider.complete(
            [
                LlmMessage(role="system", content=system_prompt),
                LlmMessage(role="user", content=_render_chunk_window(chunk)),
            ],
            model=model,
        )
    return (raw or "").strip()


async def _load_source_turns(thread_id: str) -> list[dict]:
    """standalone 调用面（未传 source_turns）：直读 ops_lg_rag_turns 原文。

    session → db 边（图谱 chat 行既有出边）；不 import lg_rag（反向边禁令）。
    失败 → 空列表（调用方 chunk 映射不符 → 降级占位），不炸请求。
    """
    try:
        # 函数内 lazy import：import 期零 DB 触网（usage.py 同款纪律）
        from app.db.models import OpsLgRagTurn
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OpsLgRagTurn)
                .where(OpsLgRagTurn.thread_id == thread_id)
                .order_by(OpsLgRagTurn.created_at.asc())
            )
            rows = result.scalars().all()
        return [{"role": row.role, "content": row.content} for row in rows]
    except Exception:
        logger.warning(
            "session summary load source turns failed thread_id=%s; keep placeholders",
            thread_id,
            exc_info=True,
        )
        return []


async def _read_cached_summary(thread_id: str, digest: str) -> str | None:
    """读缓存；**读失败视同 miss**（缓存是优化不是正确性依赖）。"""
    try:
        from app.db.models import OpsSessionSummary
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OpsSessionSummary.summary).where(
                    OpsSessionSummary.thread_id == thread_id,
                    OpsSessionSummary.chunk_hash == digest,
                )
            )
            return result.scalar_one_or_none()
    except Exception:
        logger.warning(
            "session summary cache read failed; treat as miss thread_id=%s",
            thread_id,
            exc_info=True,
        )
        return None


async def _write_cached_summary(
    *,
    thread_id: str,
    digest: str,
    summary_text: str,
    prompt_version: str,
    model: str,
    turn_count: int,
) -> None:
    """生成成功才写（get-or-create 语义）。

    唯一约束冲突 = 并发同 key 先写赢（同 key 同参数语义等价 · 容忍）；
    其它写失败 → log + 本次仍用摘要（不挡主答）。
    """
    try:
        from sqlalchemy.exc import IntegrityError

        from app.db.models import OpsSessionSummary
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            db.add(
                OpsSessionSummary(
                    thread_id=thread_id,
                    chunk_hash=digest,
                    summary=summary_text,
                    prompt_version=prompt_version,
                    model=model,
                    turn_count=turn_count,
                    source="llm",
                )
            )
            try:
                await db.commit()
            except IntegrityError:
                # 并发同 key 先写赢：冲突即容忍（本摘要语义等价，直接丢弃本次写）
                return
    except Exception:
        logger.warning(
            "session summary cache write failed (summary still used) thread_id=%s",
            thread_id,
            exc_info=True,
        )


async def summarize_placeholders(
    compressed: list[dict],
    *,
    thread_id: str,
    source_turns: list[dict] | None = None,
    max_full_turns: int = 6,
    group_size: int = 2,
    _provider: BaseProvider | None = None,
) -> list[dict]:
    """把 compress_window 产物中的占位条替换为真摘要条（结构零改动）。

    逐占位 chunk：按 chunk 源 turns 内容查缓存 → miss 才调 LLM → 写缓存。
    ``source_turns`` 缺省时直读 ops_lg_rag_turns（standalone 调用面）；
    生产路径由装配层传入已加载历史（避免二次读库）。
    任何失败 → 该 chunk 保留占位符；占位条数与 chunk 映射不符 → 整体保留占位。
    """
    result = list(compressed)
    positions = [
        i for i, t in enumerate(result) if placeholder_turn_count(t) is not None
    ]
    if not positions:
        return result

    turns = (
        source_turns if source_turns is not None else await _load_source_turns(thread_id)
    )
    chunks = derive_placeholder_chunks(
        turns, max_full_turns=max_full_turns, group_size=group_size
    )
    if chunks is None or len(chunks) != len(positions):
        logger.warning(
            "session summary chunk mapping mismatch thread_id=%s placeholders=%d; "
            "keep placeholders",
            thread_id,
            len(positions),
        )
        update_current_span_metadata({"session_summary_degraded": len(positions)})
        return result

    try:
        system_prompt, prompt_version = _resolve_prompt()
    except Exception:
        logger.exception(
            "session summary prompt asset unavailable thread_id=%s; keep placeholders",
            thread_id,
        )
        update_current_span_metadata({"session_summary_degraded": len(positions)})
        return result
    tier_model, model_display = _resolve_model()

    generated = 0
    cache_hits = 0
    degraded = 0
    for pos, chunk in zip(positions, chunks, strict=True):
        digest = chunk_content_hash(prompt_version, model_display, chunk)
        summary_text = await _read_cached_summary(thread_id, digest)
        if summary_text is not None:
            cache_hits += 1
        else:
            try:
                summary_text = await asyncio.wait_for(
                    _generate_summary(
                        system_prompt, chunk, model=tier_model, _provider=_provider
                    ),
                    timeout=SUMMARY_TIMEOUT_S,
                )
                if not summary_text:
                    raise ValueError("empty summary")
            except Exception:
                degraded += 1
                logger.warning(
                    "session summary chunk failed thread_id=%s; keep placeholder",
                    thread_id,
                    exc_info=True,
                )
                continue
            generated += 1
            await _write_cached_summary(
                thread_id=thread_id,
                digest=digest,
                summary_text=summary_text,
                prompt_version=prompt_version,
                model=model_display,
                turn_count=len(chunk),
            )
        result[pos] = {
            "role": "system",
            "content": render_summary_content(
                len(chunk), model_display, prompt_version, summary_text
            ),
        }
    update_current_span_metadata(
        {
            "session_summary_generated": generated,
            "session_summary_cache_hits": cache_hits,
            "session_summary_degraded": degraded,
        }
    )
    return result
