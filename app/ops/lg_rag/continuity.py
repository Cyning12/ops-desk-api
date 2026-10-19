"""lg-rag 窗口压缩与图输入装配（不依赖 chat/session）。

`compress_window` / `assemble_graph_messages` 保持纯函数（无 DB · 无 IO）。
事实型记忆注入（memory-facts-p0）集中在
`assemble_graph_messages_with_memory`：**默认关**（`MEMORY_FACTS_ENABLED`），
关闭时输出与 `assemble_graph_messages` 逐字节一致；开启时把召回到的
active facts 渲染为**系统消息尾部独立块**（`[已知事实]`，每条 `key=value` 一行）。
会话真摘要（session-summary-fallback）接线在同一装配面、记忆注入**之前**：
**默认关**（`SESSION_SUMMARY_ENABLED`），off / on-态全失败均与占位模式
逐字节一致；占位条内容替换走 `app/ops/session/summary.py`（经 importlib
运行期解析，守住 lg_rag 不静态依赖 session 的边界测试）。
情景记忆召回注入（host-v1-episodic-memory-feedback D3）在同一装配面、事实
注入**之后**：**默认关**（`MEMORY_EPISODES_ENABLED`），off = 装配逐字节
零 diff；on 时把同 tenant + success + active + fingerprint 匹配的相似成功
经验渲染为**独立 SystemMessage 分节**（`[相似经验]`，与 `[已知事实]`/
`[用户偏好]` 物理分节），三闸预算（条数默认 3 · 单条 ≤200 · 整块 ≤800
尾部截断）；召回失败降级不注入。

多轮指代消解查询重写（query-coref-rewrite D1）在同一装配面、两条装配分支
（session_summary on/off）**之前**一次算出 resolved_query：**默认关**
（LG_RAG_QUERY_REWRITE_ENABLED），off / 首轮无历史 / 任何失败均原文零 diff
（降级经 span 标记与「没走」区分）；末位 HumanMessage 与记忆向量召回统一
吃 resolved_query（先重写后召回 · 禁颠倒）；落盘与 run.start 仍记原文
（本面以下零感知）。实现真值在同包子模块 app.ops.lg_rag.query_rewrite。
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.ops.lg_rag.query_rewrite import maybe_rewrite_query
from app.ops.prompts.slots import (
    SlotIsolationError,
    assert_slots_declared,
    declare_slots,
    security_input_isolation_enabled,
)
from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

DEFAULT_MAX_FULL_TURNS = 6
DEFAULT_GROUP_SIZE = 2


def compress_window(
    turns: list[dict],
    *,
    max_full_turns: int = DEFAULT_MAX_FULL_TURNS,
    group_size: int = DEFAULT_GROUP_SIZE,
) -> list[dict]:
    """保留最近 ``max_full_turns`` 轮全量；更早轮次按 ``group_size`` 合并为摘要占位。

    每 turn 形如 ``{"role": "user"|"assistant"|"system", "content": str}``。
    压缩失败时降级为截断（只保留尾部 max_full_turns 轮）。
    """
    try:
        if max_full_turns <= 0 or len(turns) <= max_full_turns:
            return list(turns)
        if group_size <= 0:
            return list(turns[-max_full_turns:])

        tail = turns[-max_full_turns:]
        head = turns[:-max_full_turns]
        compressed: list[dict] = []
        for i in range(0, len(head), group_size):
            chunk = head[i : i + group_size]
            roles = {t.get("role") for t in chunk}
            compressed.append(
                {
                    "role": "system",
                    "content": (
                        f"[历史摘要 · {len(chunk)} 轮 · roles={','.join(sorted(str(r) for r in roles))}]"
                    ),
                }
            )
        return compressed + list(tail)
    except Exception:
        if max_full_turns <= 0:
            return []
        return list(turns[-max_full_turns:])


def _assemble_messages_from_compressed(query: str, compressed: list[dict]) -> list[BaseMessage]:
    """压缩产物 → LC 消息 + 本轮 HumanMessage(query)（assemble 共用内核）。"""
    messages: list[BaseMessage] = []
    for turn in compressed:
        role = (turn.get("role") or "user") if isinstance(turn, dict) else "user"
        content = ""
        if isinstance(turn, dict):
            raw = turn.get("content")
            content = raw if isinstance(raw, str) else str(raw or "")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    messages.append(HumanMessage(content=query))
    return messages


def assemble_graph_messages(
    query: str,
    history_turns: list[dict] | None = None,
    *,
    max_full_turns: int = DEFAULT_MAX_FULL_TURNS,
    group_size: int = DEFAULT_GROUP_SIZE,
) -> list[BaseMessage]:
    """历史压缩后的 LC 消息 + 本轮 HumanMessage(query)。"""
    compressed = compress_window(
        list(history_turns or []),
        max_full_turns=max_full_turns,
        group_size=group_size,
    )
    return _assemble_messages_from_compressed(query, compressed)


# ---------------- 事实型记忆注入（memory-facts-p0 · 默认关） ----------------

#: 注入块事实节首行标记；节内每条事实 `key=value` 一行
MEMORY_FACTS_HEADER = "[已知事实]"
#: 注入块偏好节首行标记（memory-preference-profile 方案 B1 单消息双节）
MEMORY_PREFERENCES_HEADER = "[用户偏好]"
#: 偏好节引导语：明示「显式陈述 / 非客观事实 / 无偏好不要假设编造」（红线③扩展；
#: 锚点断言守「用户偏好」「非客观事实」语义，改文案不挂 CI、改变量语义必挂）
MEMORY_PREFERENCES_GUIDE = (
    "用户显式陈述的偏好，用于调整回应方式；非客观事实。无偏好时不要假设或编造。"
)
DEFAULT_MEMORY_FACTS_MAX_ITEMS = 8

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")


def memory_facts_enabled() -> bool:
    """`MEMORY_FACTS_ENABLED`：默认 false；非法值回退 false + warning。"""
    raw = (os.getenv("MEMORY_FACTS_ENABLED") or "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid MEMORY_FACTS_ENABLED=%r; fallback to false", raw)
    return False


def session_summary_enabled() -> bool:
    """`SESSION_SUMMARY_ENABLED`：默认 false；非法值回退 false + warning。

    会话记忆真摘要开关（session-summary-fallback D3 铁律）：回退 = 关开关
    （零代码零迁移 · env 重读即时生效 · 进程内无缓存态）；off（未设/false/
    非法值）→ 装配输出与占位模式**逐字节一致**（对拍断言钉死）。
    """
    raw = (os.getenv("SESSION_SUMMARY_ENABLED") or "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid SESSION_SUMMARY_ENABLED=%r; fallback to false", raw)
    return False


def memory_facts_max_items() -> int:
    """`MEMORY_FACTS_MAX_ITEMS`：默认 8；非法或 ≤0 回退 8 + warning。"""
    raw = (os.getenv("MEMORY_FACTS_MAX_ITEMS") or "").strip()
    if not raw:
        return DEFAULT_MEMORY_FACTS_MAX_ITEMS
    try:
        n = int(raw)
    except ValueError:
        logger.warning(
            "invalid MEMORY_FACTS_MAX_ITEMS=%r; fallback to %d",
            raw,
            DEFAULT_MEMORY_FACTS_MAX_ITEMS,
        )
        return DEFAULT_MEMORY_FACTS_MAX_ITEMS
    if n <= 0:
        logger.warning(
            "MEMORY_FACTS_MAX_ITEMS=%r <= 0; fallback to %d",
            raw,
            DEFAULT_MEMORY_FACTS_MAX_ITEMS,
        )
        return DEFAULT_MEMORY_FACTS_MAX_ITEMS
    return n


# ---------------- 情景记忆召回注入（host-v1-episodic-memory-feedback D3 · 默认关） ----------------

#: 注入块经验节首行标记；与 [已知事实]/[用户偏好] **物理分节**（独立 SystemMessage）
MEMORY_EPISODES_HEADER = "[相似经验]"
DEFAULT_MEMORY_EPISODES_MAX_ITEMS = 3
#: 三闸预算（SPEC Q3 裁定）：单条 ≤200（承 MAX_VALUE_CHARS）· 整块 ≤800
#:（承 step_contract MAX_CONTEXT_BLOCK_CHARS：单值截断挡不住累加，故设整块闸）
EPISODE_ITEM_MAX_CHARS = 200
EPISODE_BLOCK_MAX_CHARS = 800


def memory_episodes_enabled() -> bool:
    """`MEMORY_EPISODES_ENABLED`：默认 false；非法值回退 false + warning。

    情景记忆召回注入开关（host-v1-episodic-memory-feedback D3 纪律 2 双开关
    之一；写开关 MEMORY_EPISODES_WRITE_ENABLED 在 episode_service）：off →
    装配输出与现网**逐字节一致**（对拍断言钉死）。
    """
    raw = (os.getenv("MEMORY_EPISODES_ENABLED") or "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid MEMORY_EPISODES_ENABLED=%r; fallback to false", raw)
    return False


def memory_episodes_max_items() -> int:
    """`MEMORY_EPISODES_MAX_ITEMS`：默认 3；非法或 ≤0 回退 3 + warning。"""
    raw = (os.getenv("MEMORY_EPISODES_MAX_ITEMS") or "").strip()
    if not raw:
        return DEFAULT_MEMORY_EPISODES_MAX_ITEMS
    try:
        n = int(raw)
    except ValueError:
        logger.warning(
            "invalid MEMORY_EPISODES_MAX_ITEMS=%r; fallback to %d",
            raw,
            DEFAULT_MEMORY_EPISODES_MAX_ITEMS,
        )
        return DEFAULT_MEMORY_EPISODES_MAX_ITEMS
    if n <= 0:
        logger.warning(
            "MEMORY_EPISODES_MAX_ITEMS=%r <= 0; fallback to %d",
            raw,
            DEFAULT_MEMORY_EPISODES_MAX_ITEMS,
        )
        return DEFAULT_MEMORY_EPISODES_MAX_ITEMS
    return n


def _fact_key_value(item: Any) -> tuple[str, Any]:
    """兼容 ORM 行与 dict（service 返回 ORM；测试可传 dict）。"""
    if isinstance(item, Mapping):
        return str(item.get("key") or ""), item.get("value")
    return str(getattr(item, "key", "") or ""), getattr(item, "value", None)


def _fact_kind(item: Any) -> str:
    """取 kind（兼容 ORM 行与 dict）；缺省按 fact 兜底——闸 + CHECK 保证
    落库行 kind ∈ {fact, preference}，缺 kind 的测试 dict 即旧事实语义。"""
    if isinstance(item, Mapping):
        return str(item.get("kind") or "fact")
    return str(getattr(item, "kind", None) or "fact")


def _render_rows(items: list[Any]) -> list[str]:
    """每条 `key=value` 一行：str 直写（换行转义 \\n），其它标量 JSON 序列化。"""
    rows: list[str] = []
    for item in items:
        key, value = _fact_key_value(item)
        text = (
            value.replace("\n", "\\n")
            if isinstance(value, str)
            else json.dumps(value, ensure_ascii=False)
        )
        rows.append(f"{key}={text}")
    return rows


def render_memory_facts_block(facts: list[Any]) -> str:
    """渲染注入块（memory-preference-profile 方案 B1 单块双节）：`[已知事实]` 节 + `[用户偏好]` 节。

    - kind=fact 行进事实节，kind=preference 行进偏好节，**互不串节**
      （偏好污染事实通路 = 静默错，分节单测钉死）。
    - **无 preference → 偏好节物理不存在**（幻觉偏好红线结构断言落点）；
      无 fact → 事实节同样不出现；空集 → 空串不注入（现行为沿用）。
    - fact-only 输入渲染与 P0 现网**逐字节一致**（对拍断言钉死）。
    """
    if not facts:
        return ""
    pref_items = [item for item in facts if _fact_kind(item) == "preference"]
    fact_items = [item for item in facts if _fact_kind(item) != "preference"]
    sections: list[str] = []
    if fact_items:
        sections.append("\n".join([MEMORY_FACTS_HEADER, *_render_rows(fact_items)]))
    if pref_items:
        sections.append(
            "\n".join(
                [MEMORY_PREFERENCES_HEADER, MEMORY_PREFERENCES_GUIDE, *_render_rows(pref_items)]
            )
        )
    return ("\n" + "\n").join(sections)


def _episode_summary_tools(item: Any) -> tuple[str, list[str]]:
    """取 (plan_summary, tool_sequence)（兼容 ORM 行与 dict，承 _fact_key_value 先例）。"""
    if isinstance(item, Mapping):
        summary = str(item.get("plan_summary") or "")
        tools = item.get("tool_sequence")
    else:
        summary = str(getattr(item, "plan_summary", "") or "")
        tools = getattr(item, "tool_sequence", None)
    tool_ids = [str(t) for t in tools if isinstance(t, str)] if isinstance(tools, list) else []
    return summary, tool_ids


def render_memory_episodes_block(episodes: list[Any]) -> str:
    """渲染 `[相似经验]` 独立分节块（host-v1-episodic-memory-feedback D3 · Q3 三闸预算）。

    - 每条经验一行：`- {plan_summary}｜工具: {id1,id2}`（结构元数据非用户内容；
      摘要内换行转义 \\n 保住一行一条）。
    - **单条闸**：行 >200 字符 → 尾部截断加 …（承 MAX_VALUE_CHARS 先例）。
    - **整块闸**：header+各行 >800 字符 → 从尾部丢低优先级行（召回序 =
      created_at desc，尾部即最旧）；首条都装不下时硬截进预算
      （宁少给，不超预算 · 承 step_contract :28-30 先例）。
    - 空集 → 空串不注入；本块与 [已知事实]/[用户偏好] **物理分节**
      （独立 SystemMessage · 分节断言钉死）。
    """
    if not episodes:
        return ""
    lines = [MEMORY_EPISODES_HEADER]
    used = len(MEMORY_EPISODES_HEADER)
    for item in episodes:
        summary, tool_ids = _episode_summary_tools(item)
        line = f"- {summary.replace(chr(10), chr(92) + 'n')}｜工具: {','.join(tool_ids)}"
        if len(line) > EPISODE_ITEM_MAX_CHARS:
            line = line[: EPISODE_ITEM_MAX_CHARS - 1] + "…"
        if used + len(line) + 1 > EPISODE_BLOCK_MAX_CHARS:
            if len(lines) == 1:
                room = EPISODE_BLOCK_MAX_CHARS - used - 1
                lines.append(line[: max(0, room - 1)] + "…")
            break
        lines.append(line)
        used += len(line) + 1
    if len(lines) == 1:
        return ""
    return "\n".join(lines)


def inject_memory_facts_block(messages: list[BaseMessage], block: str) -> list[BaseMessage]:
    """把块作为**独立 SystemMessage** 插到既有前缀系统消息之后（无则置队首）。

    空块原样返回（零 diff）；不掺入任何 prompt 模板 / 指令正文。
    """
    if not block:
        return messages
    idx = 0
    for msg in messages:
        if isinstance(msg, SystemMessage):
            idx += 1
        else:
            break
    return [*messages[:idx], SystemMessage(content=block), *messages[idx:]]


async def _assemble_with_session_summary(
    query: str,
    history_turns: list[dict] | None,
    *,
    thread_id: str | None,
    max_full_turns: int,
    group_size: int,
) -> list[BaseMessage]:
    """真摘要面接线（session-summary-fallback D1 · 仅在开关 on 时触达）。

    结构仍由 compress_window 定（**零改动**）；占位条内容替换走
    app.ops.session.summary。lg_rag → app.ops.session 静态 import 被边界
    测试禁止（tests/test_lg_rag_session_continuity.py「禁止 import
    app.ops.session / app.ops.chat」），故经 importlib **运行期解析**
    （on 态才触达；off 态静态加载链零变化）。解析/摘要任何失败 →
    占位模式逐字节回退 + span session_summary_degraded=N。
    """
    turns = list(history_turns or [])
    compressed = compress_window(turns, max_full_turns=max_full_turns, group_size=group_size)
    if not (thread_id or "").strip():
        logger.warning("SESSION_SUMMARY_ENABLED on but thread_id missing; keep placeholders")
    else:
        try:
            import importlib

            session_summary = importlib.import_module("app.ops.session.summary")
            compressed = await session_summary.summarize_placeholders(
                compressed,
                thread_id=(thread_id or "").strip(),
                source_turns=turns,
                max_full_turns=max_full_turns,
                group_size=group_size,
            )
        except Exception:
            n_placeholders = sum(
                1
                for t in compressed
                if isinstance(t, dict) and str(t.get("content") or "").startswith("[历史摘要 · ")
            )
            logger.exception("session summary face failed; keep placeholders")
            update_current_span_metadata({"session_summary_degraded": n_placeholders})
    return _assemble_messages_from_compressed(query, compressed)


async def _assemble_graph_messages_with_memory_impl(
    query: str,
    history_turns: list[dict] | None = None,
    *,
    tenant_id: str | None = None,
    user_id: str | None = None,
    thread_id: str | None = None,
    task_domain: str | None = None,
    intent_features: dict | None = None,
    tool_sequence: list[str] | None = None,
    max_full_turns: int = DEFAULT_MAX_FULL_TURNS,
    group_size: int = DEFAULT_GROUP_SIZE,
) -> list[BaseMessage]:
    """装配 + 可选真摘要 + 可选记忆注入。**开关全关时与 assemble_graph_messages 逐字节一致。**

    摘要面（session-summary-fallback · `SESSION_SUMMARY_ENABLED` 默认关）：
    接线在记忆注入**之前**；off（未设/false/非法值）→ 跳过本面，与现网
    **逐字节一致**（off 三态对拍断言钉死）；on 态任何失败 → 该 chunk 保留
    占位符降级（span `session_summary_degraded=N`），与 off 态逐字节一致。
    thread_id 仅供摘要缓存 key（身份取自请求上下文既有校验链）。

    身份纪律：tenant/user 由调用方从请求 ctx 取（tenant_context ContextVar /
    阶段 T 头校验链路 / session 用户）后**显式传入**；模型产出不得参与。
    召回故障 → 记 log + span `memory_degraded`，降级为不注入（不拖垮请求）。
    span metadata 记 `memory_facts_injected=N`；有 preference 时并列
    `memory_preferences_injected=M`（tracing 未开时静默 no-op）。
    """
    # query-coref-rewrite D1（先重写后召回 · 钉死顺序）：resolved_query 在两条
    # 装配分支（session_summary on/off）之前一次算出；末位 HumanMessage（经下方
    # 两分支统一）与记忆向量召回统一吃它；off / 首轮无历史 / 任何失败 → 原文
    # 零 diff（降级经 span query_rewrite_fallback=true 与「没走」区分）。
    resolved_query = await maybe_rewrite_query(query, history_turns)
    if session_summary_enabled():
        messages = await _assemble_with_session_summary(
            resolved_query,
            history_turns,
            thread_id=thread_id,
            max_full_turns=max_full_turns,
            group_size=group_size,
        )
    else:
        messages = assemble_graph_messages(
            resolved_query,
            history_turns,
            max_full_turns=max_full_turns,
            group_size=group_size,
        )
    if memory_facts_enabled():
        if not (tenant_id or "").strip() or not (user_id or "").strip():
            logger.warning("MEMORY_FACTS_ENABLED on but tenant/user missing; skip injection")
        else:
            try:
                # 延迟 import：continuity 保持纯函数可独立加载；memory 依赖 db
                from app.ops.memory import service as memory_service

                if memory_service.memory_facts_vector_recall_enabled():
                    # P1 混合召回（默认关）：确定性 top-N ∪ 向量 top-M → 融合排序；
                    # 向量通路失败内部回退确定性 + memory_vector_degraded
                    facts = await memory_service.recall_with_vector(
                        tenant_id.strip(),
                        user_id.strip(),
                        resolved_query,
                        limit=memory_facts_max_items(),
                    )
                else:
                    facts = await memory_service.recall_active(
                        tenant_id.strip(),
                        user_id.strip(),
                        limit=memory_facts_max_items(),
                    )
            except Exception:
                logger.exception("memory facts recall failed; degrade to no injection")
                update_current_span_metadata({"memory_degraded": True})
            else:
                if not facts:
                    update_current_span_metadata({"memory_facts_injected": 0})
                else:
                    block = render_memory_facts_block(facts)
                    # span 双计数（D2）：facts/preferences 分别记；preference 为 0 时不出
                    # 该 key（fact-only 流量与 P0/P1 观测面逐字节一致）
                    n_prefs = sum(1 for f in facts if _fact_kind(f) == "preference")
                    span: dict[str, Any] = {"memory_facts_injected": len(facts) - n_prefs}
                    if n_prefs:
                        span["memory_preferences_injected"] = n_prefs
                    update_current_span_metadata(span)
                    messages = inject_memory_facts_block(messages, block)

    # ---------------- 情景记忆召回注入（D3 · 默认关 · 独立分节） ----------------
    if not memory_episodes_enabled():
        return messages
    if not (tenant_id or "").strip():
        logger.warning("MEMORY_EPISODES_ENABLED on but tenant missing; skip episode injection")
        return messages
    try:
        # 延迟 import（同 memory service 先例）：off 态静态加载链零变化
        from app.ops.memory import episode_gate, episode_service

        # 当前意图 fingerprint 与写入同规则计算（domain+意图特征+工具序列骨架）
        fingerprint = episode_gate.compute_context_fingerprint(
            task_domain or "", intent_features, tool_sequence
        )
        episodes = await episode_service.recall_success_episodes(
            tenant_id.strip(),
            fingerprint,
            limit=memory_episodes_max_items(),
        )
    except Exception:
        # 召回失败降级不注入（承 :369 事实召回先例），不拖垮请求
        logger.exception("memory episodes recall failed; degrade to no injection")
        update_current_span_metadata({"memory_episodes_degraded": True})
        return messages
    if not episodes:
        update_current_span_metadata({"memory_episodes_injected": 0})
        return messages
    episode_block = render_memory_episodes_block(episodes)
    # span 记注入条数（tracing 未开时静默 no-op，承 memory_facts_injected 先例）
    update_current_span_metadata({"memory_episodes_injected": len(episodes)})
    # 独立 SystemMessage 分节：插在前缀系统消息（含事实块）之后
    return inject_memory_facts_block(messages, episode_block)


# ---------------- 输入结构隔离边界（security-input-isolation W1 · 默认关） ----------------


def _attribute_isolation_slots(messages: list[BaseMessage]) -> list[BaseMessage]:
    """消息级槽位归因（纯函数 · 仅 on 态触达）：角色序与正文零改动。

    - 末条 HumanMessage（本轮问题）→ `user_query`；
    - memory 注入块（`[已知事实]`/`[用户偏好]` 节首的 SystemMessage）→ `memory_fact`
      （语义不变 · 声明补全）；
    - 其余历史/压缩占位消息 → `history_turn`。
    """
    attributed: list[BaseMessage] = []
    last = len(messages) - 1
    for i, msg in enumerate(messages):
        content = str(msg.content)
        if isinstance(msg, SystemMessage) and (
            content.startswith(MEMORY_FACTS_HEADER)
            or content.startswith(MEMORY_PREFERENCES_HEADER)
            or content.startswith(MEMORY_EPISODES_HEADER)
        ):
            slot_id = "memory_fact"
        elif i == last and isinstance(msg, HumanMessage):
            slot_id = "user_query"
        else:
            slot_id = "history_turn"
        attributed.append(declare_slots(msg, [slot_id]))
    return attributed


async def assemble_graph_messages_with_memory(
    query: str,
    history_turns: list[dict] | None = None,
    *,
    tenant_id: str | None = None,
    user_id: str | None = None,
    thread_id: str | None = None,
    task_domain: str | None = None,
    intent_features: dict | None = None,
    tool_sequence: list[str] | None = None,
    max_full_turns: int = DEFAULT_MAX_FULL_TURNS,
    group_size: int = DEFAULT_GROUP_SIZE,
) -> list[BaseMessage]:
    """装配 + 可选真摘要 + 可选记忆注入 + 可选输入结构隔离边界。

    装配语义见 `_assemble_graph_messages_with_memory_impl`；开关全关时与
    `assemble_graph_messages` **逐字节一致**。

    输入结构隔离（security-input-isolation D2 · `SECURITY_INPUT_ISOLATION_ENABLED`
    默认关）：on 态对装配产物做消息级槽位归因（`history_turn`/`user_query`/
    `memory_fact` · 角色序与正文零改动）并在发往图前执行
    `assert_slots_declared` 纯函数校验——内容违例（未声明段）→
    :class:`SlotIsolationError` 显式炸，**请求不进入图**（下游零请求）+
    span `input_isolation_rejected`；机制自身故障 → 该请求降级 off 态装配
    + span `input_isolation_degraded`（两语义分立断言）。off 态校验零触达
    （包装/校验调用计数 = 0）。
    """
    messages = await _assemble_graph_messages_with_memory_impl(
        query,
        history_turns,
        tenant_id=tenant_id,
        user_id=user_id,
        thread_id=thread_id,
        task_domain=task_domain,
        intent_features=intent_features,
        tool_sequence=tool_sequence,
        max_full_turns=max_full_turns,
        group_size=group_size,
    )
    if not security_input_isolation_enabled():
        return messages
    try:
        attributed = _attribute_isolation_slots(messages)
        assert_slots_declared(attributed)
        update_current_span_metadata({"slots_wrapped": len(attributed)})
        return attributed
    except SlotIsolationError:
        update_current_span_metadata({"input_isolation_rejected": True})
        logger.warning(
            "input isolation rejected undeclared content; request rejected before graph",
            exc_info=True,
        )
        raise
    except Exception:
        logger.exception("input isolation mechanism failed; degrade to off-state assembly")
        update_current_span_metadata({"input_isolation_degraded": True})
        return messages
