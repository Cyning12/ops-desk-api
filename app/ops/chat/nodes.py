"""LangGraph Chat 节点：纯业务函数，只读/写 ChatState，不依赖 FastAPI。

约定：
- 每个节点返回「局部更新 dict」，由 LangGraph merge 进 ChatState
- events 字段带 Annotated[..., add] 累加，供 SSE/WS 流式推送
"""
import re

from sqlalchemy import select

from app.config import settings
from app.db.models import OpsIssue
from app.db.session import AsyncSessionLocal
from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage, LlmProviderError, LlmUsage
from app.ops.chat.state import ChatState
from app.ops.rag.grader import REFUSAL_TEXT
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.tracing import trace_span, update_current_generation_usage

# 与 _build_messages 注入的「资料」块 + 契约 4c 引用/拒答对齐
_SYSTEM_PROMPT = (
    "### 角色声明\n"
    "你是 Ops Desk 助手，专为供应商运营与销售团队提供技术知识问答支持。\n"
    "\n"
    "### 任务边界\n"
    "你的知识来源仅限于后续消息中提供的「资料」"
    "（含 issue 上下文或检索命中块），不得使用外部知识或训练数据中的记忆。\n"
    "\n"
    "### 关键约束\n"
    "- 必须基于资料作答，不得编造或扩展。\n"
    "- 若后续消息已注明「仅部分证据」：仍须作答，开头写明「仅部分证据」，"
    "只陈述资料已覆盖部分，未覆盖处不要猜测。\n"
    "- 若无资料、或资料与问题无关：直接拒答，不要尝试猜测。\n"
    "- 准确性优先于简洁性——若精简会丢失关键信息，请保留完整细节。\n"
    "\n"
    "### 输出格式\n"
    "- 引用来源用 [类型 编号] 标注，与资料标题一致"
    "（如 [issue 2720]、[doc contracts/xx.md]、[pr 123]）。\n"
    "- 若资料中存在多个观点或版本，请分别说明并标注对应引用。\n"
    "- 若资料含代码片段，回答中保留原格式（```）。\n"
    "\n"
    "### 兜底行为\n"
    "需要拒答时，直接输出以下原文，不要解释原因：\n"
    f"\"{REFUSAL_TEXT}\"\n"
)


async def intent_node(state: ChatState) -> dict:
    """识别用户意图，写入 state.intent，供条件边路由。

    规则（轻量启发式，非 LLM）：
    - 含 #数字 → issue_qa
    - 含「总览」/overview → overview
    - 其余 → general
    """
    query = state["query"]
    intent = "general"
    if re.search(r"#\d+", query):
        intent = "issue_qa"
    elif "总览" in query or "overview" in query.lower():
        intent = "overview"

    return {
        "intent": intent,
        "events": [
            {
                "event_type": "thinking",
                "agent_role": "intent",
                "payload": {"content": f"识别意图为 {intent}", "step": "intent"},
            }
        ],
    }


def route_by_intent(state: ChatState) -> str:
    """条件边回调：返回下一跳 key（须与 graph.add_conditional_edges 映射一致）。"""
    return state["intent"]


async def _fetch_issue_by_number(number: int) -> dict | None:
    """按 GitHub issue number 查库，返回精简 dict；未找到则 None。"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OpsIssue).where(OpsIssue.number == number))
        issue = result.scalar_one_or_none()
        if issue is None:
            return None
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "state": issue.state,
            "labels": issue.labels or [],
            "module_tag": issue.module_tag,
            "html_url": issue.html_url,
        }


async def load_issue_context_node(state: ChatState) -> dict:
    """从 query 提取 #N，加载 issue 上下文到 state.issue_context。

    仅 issue_qa 路径会到达本节点；查库失败不抛出，以 tool_result 事件上报。
    """
    match = re.search(r"#(\d+)", state["query"])
    issue_number = int(match.group(1)) if match else None
    issue: dict | None = None
    summary = "未识别到 issue 编号"

    if issue_number is not None:
        try:
            issue = await _fetch_issue_by_number(issue_number)
            summary = issue["title"] if issue else "未找到"
        except Exception as exc:  # pragma: no cover - defensive; DB failures are logged by caller
            summary = f"查询失败: {exc}"

    return {
        "issue_context": [issue] if issue else [],
        "events": [
            {
                "event_type": "tool_result",
                "agent_role": "context",
                "payload": {
                    "tool": "load_issue",
                    "ok": issue is not None,
                    "issue_number": issue_number,
                    "summary": summary,
                },
            }
        ],
    }


def _build_messages(state: ChatState) -> list[LlmMessage]:
    """组装 OpenAI 兼容 messages：system + 可选 issue/检索资料 + 用户 query。

    引用格式与拒答话术以 _SYSTEM_PROMPT / REFUSAL_TEXT 为准；本函数只注入资料正文。
    """
    messages: list[LlmMessage] = [LlmMessage(role="system", content=_SYSTEM_PROMPT)]

    for turn in state.get("history_turns") or []:
        role = str(turn.get("role") or "user")
        content = str(turn.get("content") or "").strip()
        if not content:
            continue
        if role not in ("user", "assistant", "system"):
            role = "user"
        messages.append(LlmMessage(role=role, content=content))

    issue_context = state.get("issue_context") or []
    if issue_context:
        issue = issue_context[0]
        # body 截断，避免撑爆上下文窗口
        body = (issue.get("body") or "")[:2000]
        num = issue.get("number")
        messages.append(
            LlmMessage(
                role="user",
                content=(
                    f"### 资料 [issue {num}]\n"
                    f"标题：{issue.get('title')}\n{body}"
                ),
            )
        )

    # R-3 检索链上下文（general/overview 路径）：命中块（契约 4c/T13）
    retrieved = state.get("retrieved") or []
    if retrieved:
        parts = [
            f"### 资料 [{c.source_type} {c.anchor}]\n"
            f"{strip_doc_context_prefix(c.content)[:1200]}"
            for c in retrieved
        ]
        header = "以下是与问题相关的资料：\n\n" + "\n\n".join(parts)
        if state.get("gate_action") == "answer_partial":
            header += (
                "\n\n重要：现有证据仅覆盖问题的一部分；"
                "请按系统约束作答，开头注明「仅部分证据」，不要因此拒答。"
            )
        messages.append(LlmMessage(role="user", content=header))

    messages.append(LlmMessage(role="user", content=state["query"]))
    return messages


async def answer_node(state: ChatState) -> dict:
    """调用 LLM 流式生成最终回答；token/fallback/error 均写入 events。"""
    provider = get_llm_provider()
    model = state.get("model") or settings.ops_llm_model
    messages = _build_messages(state)

    events: list[dict] = [
        {
            "event_type": "thinking",
            "agent_role": "answer",
            "payload": {"content": "准备生成回答...", "step": "answer"},
        }
    ]
    answer_parts: list[str] = []

    try:
        # 手动 generation 观测：自研 provider 不走 LangChain LLM 类，
        # CallbackHandler 抓不到这次调用，需显式包裹（Langfuse 技能基线：LLM 调用必须是 generation）
        with trace_span("answer_llm", run_type="llm", model=model):
            async for chunk in provider.complete_stream(messages, model=model):
                # include_usage 末帧：上报 token 用量到 generation（观测基线）
                if chunk.meta and chunk.meta.get("usage"):
                    parsed = LlmUsage.from_provider_usage(chunk.meta["usage"])
                    if parsed is not None:
                        update_current_generation_usage(parsed)
                    continue
                # Provider 可能在流中插入 fallback 元事件，与正文 chunk 分流
                if chunk.meta and chunk.meta.get("event_type") == "model.fallback":
                    events.append(
                        {
                            "event_type": "model.fallback",
                            "agent_role": "answer",
                            "payload": chunk.meta,
                        }
                    )
                else:
                    answer_parts.append(chunk.content)
                    events.append(
                        {
                            "event_type": "answer",
                            "agent_role": "answer",
                            "payload": {"content": chunk.content},
                        }
                    )
    except Exception as exc:
        retryable = isinstance(exc, LlmProviderError) and exc.retryable
        events.append(
            {
                "event_type": "error",
                "agent_role": "answer",
                "payload": {"stage": "llm", "message": str(exc), "retryable": retryable},
            }
        )

    return {"answer": "".join(answer_parts), "events": events}
