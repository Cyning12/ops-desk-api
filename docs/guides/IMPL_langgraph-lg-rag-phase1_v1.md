# 实现辅助：LangGraph lg_rag Phase 1（基础单 Agent · v1）

> **与 task / 总纲的关系**：本文件 = **30 手写说明书（Phase 1）**。  
> - 总纲：`docs/guides/PLAN-langgraph-agent-framework_v1.md`  
> - 上游资产：`app/ops/lc_evidence_chain/`（`ainvoke_evidence_answer`）  
> - task：尚未创建时 **仅作设计指导，禁止本文件单独驱动改码**；开工前须有  
>   `docs/tasks/active/task_*.md` 且人工闸 `approved`。  
> **读者**：维护者本人按阶段实现。  
> **硬约束**：  
> 1. **不要改** `app/ops/chat/graph.py` 的节点与边（Chat 现网图保持不动）。  
> 2. **不要拆散** `lc_evidence_chain` 的 retrieve/grade/answer；Phase 1 整链当黑盒 Node。  
> 3. 包落在已有空壳 `app/ops/lg_rag/`（勿新建平行包名）。

---

## 总览

目标拓扑（Phase 1 最小图）：

```text
input: HumanMessage(query) + config.thread_id
  → rag_node          # 黑盒调用 ainvoke_evidence_answer
  → END
output: messages 末条 AIMessage(answer)
  + Checkpointer 快照（InMemory → Postgres）
```

与 LCEL 旁路的关系：

```text
lc_evidence_chain.ainvoke_evidence_answer  ──黑盒复用──▶  lg_rag.rag_node
chat/graph.py（现网 SSE）                 ──本期不碰──▶  （并行共存）
```

建议目录：

```text
app/ops/lg_rag/
  __init__.py         # export build_basic_agent, ainvoke_basic_agent
  nodes.py            # rag_node
  graph.py            # StateGraph 组装 + compile
  checkpointer.py     # memory / postgres 工厂（可后置）
scripts/lg_rag_smoke.py
tests/test_lg_rag_basic.py
```

Phase 1 验收对照（摘自总纲，实现时以 task 表为准）：

| ID | 产出 | 验收 |
|---|---|---|
| 1.1 | 依赖 | `langgraph` 已有；补 `langgraph-checkpoint-postgres`（版本与 `langgraph>=0.2,<0.3` 兼容） |
| 1.2 | `rag_node` | 单 Query 走通完整 LCEL RAG |
| 1.3 | `build_basic_agent()` | 本地 `ainvoke` 得到非空 answer |
| 1.4 | Checkpointer | 先 InMemory 冒烟；再 PG：同 `thread_id` 可续写 messages |
| 1.5 | Langfuse | UI 可见 tag/`run_name`=`lg-rag`（或约定名）执行树 |
| 1.6 | Golden / 回归 | **至少**与直连 `ainvoke_evidence_answer` **答案对齐**（同 query）；全量 73 条基线 ≥ 现网 RAG 报告时另开评测入口 |

---

## S0 · 骨架

**目标**：包可 import；与空文件 `app/ops/lg_rag/__init__.py` / `graph.py` 对齐填实。

示例 `__init__.py`：

```python
"""LangGraph 旁路：Evidence Chain 封装为单 Agent（默认不挂 chat/graph）。"""

from app.ops.lg_rag.graph import ainvoke_basic_agent, build_basic_agent

__all__ = ["build_basic_agent", "ainvoke_basic_agent"]
```

**自检**：

```bash
.venv/bin/python -c "from app.ops.lg_rag import build_basic_agent"
```

---

## S1 · 依赖与 Checkpointer 选型

**现状（落盘时）**：

- `requirements.txt` / `pyproject.toml` 已有 `langgraph>=0.2,<0.3`
- **尚无** `langgraph-checkpoint-postgres`（本机 `import langgraph.checkpoint.postgres` 会失败）
- 内存检查点：`from langgraph.checkpoint.memory import InMemorySaver`（`MemorySaver` 为其别名）

**建议顺序**：

1. S2–S3 全程用 `InMemorySaver`，不阻塞骨架。  
2. S5 再加可选依赖与 `PostgresSaver` / `AsyncPostgresSaver`。  
3. 异步服务优先调研 `AsyncPostgresSaver`（仓内 FastAPI + asyncpg）；若官方示例以同步 `PostgresSaver` + `from_conn_string` 为主，Phase 1 允许同步 checkpointer + 异步 node（与多数教程一致），并在 task 备注风险。

依赖追加示意（版本号以实现时 PyPI 兼容矩阵为准，勿照抄锁死）：

```text
# requirements.txt / pyproject.toml
langgraph-checkpoint-postgres>=1.0,<3
# 常见还需 psycopg[binary]（仓内已有 psycopg）
```

**自检**：

```bash
.venv/bin/python -c "from langgraph.checkpoint.memory import InMemorySaver; print(InMemorySaver)"
# 装 PG 包后：
.venv/bin/python -c "from langgraph.checkpoint.postgres import PostgresSaver"
```

---

## S2 · 封装 `rag_node`

**原则**：只调 `ainvoke_evidence_answer`；不复制 retrieve SQL / grader / answer prompt。

示例 `nodes.py`：

```python
from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import MessagesState

from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer


def _last_user_text(messages: list[BaseMessage]) -> str:
    for m in reversed(messages):
        if getattr(m, "type", None) == "human" or m.__class__.__name__ == "HumanMessage":
            content = m.content
            return content if isinstance(content, str) else str(content)
    raise ValueError("messages 中无 HumanMessage")


async def rag_node(state: MessagesState) -> dict:
    """黑盒 RAG：LCEL evidence chain → 追加一条 AIMessage。"""
    query = _last_user_text(state["messages"])
    result = await ainvoke_evidence_answer(query)
    # ChainResult 为 Pydantic：用 .answer；勿写成 result["answer"]
    return {"messages": [AIMessage(content=result.answer or "")]}
```

> **注意**：`MessagesState` 的 `messages` 使用 `add_messages` reducer，返回「增量」列表即可，不要手写全量覆盖。

**自检**（mock chain，不连库）：见 S6。

---

## S3 · 最小 StateGraph + InMemorySaver

示例 `graph.py`：

```python
from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from app.ops.lg_rag.nodes import rag_node


def build_basic_agent(*, checkpointer: Any | None = None):
    """START → rag → END；默认 InMemorySaver。"""
    builder = StateGraph(MessagesState)
    builder.add_node("rag", rag_node)
    builder.add_edge(START, "rag")
    builder.add_edge("rag", END)
    saver = checkpointer if checkpointer is not None else InMemorySaver()
    return builder.compile(checkpointer=saver)


async def ainvoke_basic_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
) -> dict[str, Any]:
    graph = build_basic_agent(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id[:255]}}
    return await graph.ainvoke(
        {"messages": [HumanMessage(content=query)]},
        config,
    )
```

> 旧 API `set_entry_point` / `set_finish_point` 仍可用；新代码优先 `START` / `END` 显式边（与 `app/ops/chat/graph.py` 风格一致）。

**自检**（需 db + 向量 + LLM，或先 mock）：

```bash
.venv/bin/python -c "
import asyncio
from app.ops.lg_rag import ainvoke_basic_agent
out = asyncio.run(ainvoke_basic_agent('自动压缩被取消怎么办', thread_id='t1'))
print(out['messages'][-1].content[:200])
"
```

---

## S4 · Langfuse 回调

**对齐现网**：

- Chat：`app/ops/chat/service.py` · `_trace_config` → `CallbackHandler` + tags=`ops-chat`
- LCEL：`app/ops/lc_evidence_chain/chain.py` · `_trace_config` + `trace_span("lc-evidence-chain")`

Phase 1 建议在 `ainvoke_basic_agent`（或薄封装 `invoke`）注入 config，**不要**改 Chat service：

```python
from contextlib import nullcontext

from app.ops.tracing import (
    ensure_langfuse_environment,
    flush_traces,
    trace_span,
    tracing_enabled,
)

_RUN_NAME = "lg-rag"
_TAG = "lg-rag"


def _trace_config(*, thread_id: str | None = None) -> dict | None:
    if not tracing_enabled():
        return None
    ensure_langfuse_environment()
    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        return None
    metadata: dict = {"langfuse_tags": [_TAG]}
    if thread_id:
        metadata["langfuse_session_id"] = thread_id
    return {
        "callbacks": [CallbackHandler()],
        "metadata": metadata,
        "run_name": _RUN_NAME,
    }


async def ainvoke_basic_agent(query: str, *, thread_id: str = "lg-rag-smoke", **kw):
    graph = build_basic_agent(**kw)
    config: dict = {"configurable": {"thread_id": thread_id[:255]}}
    if tc := _trace_config(thread_id=thread_id):
        # 合并 callbacks / metadata / run_name；勿丢掉 thread_id
        config = {**tc, "configurable": config["configurable"]}
    span_cm = (
        trace_span(_RUN_NAME, run_type="chain", tags=[_TAG])
        if tracing_enabled()
        else nullcontext()
    )
    with span_cm:
        return await graph.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config,
        )
```

**自检**：

1. `.env`：`OPS_CHAT_TRACER=langfuse` + `LANGFUSE_*`（本机 `LANGFUSE_ENV=dev`）。  
2. 跑 smoke 后 `flush_traces()`。  
3. Langfuse UI 同 environment 下筛选 tag `lg-rag`；应能看到图/节点，且内层 LCEL 仍可能带 `lc-evidence-chain` 子树（可接受；勿强行关掉上游 tracing）。

---

## S5 · PostgresSaver（可后于 InMemory）

示例 `checkpointer.py`（示意；以装包后的官方 API 为准）：

```python
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from app.config import settings


@contextmanager
def postgres_saver() -> Iterator[object]:
    """同步 PostgresSaver 上下文；调用方负责 setup() 一次。"""
    from langgraph.checkpoint.postgres import PostgresSaver

    # DATABASE_URL 若为 postgresql+asyncpg:// 需改成 psycopg 可认的 DSN
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    with PostgresSaver.from_conn_string(dsn) as checkpointer:
        checkpointer.setup()  # 建表；生产应迁到 Alembic / 启动钩子只跑一次
        yield checkpointer
```

续写自检逻辑：

```python
# 同 thread_id 第二次 ainvoke 时，state.messages 应含上一轮 Human+AI
```

**坑**：

| 坑 | 处理 |
|---|---|
| `thread_id` 过长 | 截断 ≤ 255 或改用 UUID |
| 表未创建 | 必须 `setup()` 或等价迁移 |
| asyncpg DSN | checkpointer 通常要 **psycopg** DSN，勿直接塞 `+asyncpg` |
| 与业务表混库 | Phase 1 可同库不同表；表名前缀由库默认 `checkpoints` 等 |

---

## S6 · CLI 冒烟

示例 `scripts/lg_rag_smoke.py`（对齐 `scripts/lc_evidence_smoke.py`）：

```python
#!/usr/bin/env python3
"""lg_rag Phase1 冒烟：StateGraph → rag_node → Evidence Chain。"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from app.ops.lg_rag import ainvoke_basic_agent
from app.ops.tracing import flush_traces, tracing_enabled

DEFAULT_QUERY = "Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因?"


async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", default=DEFAULT_QUERY)
    p.add_argument("--thread-id", default="lg-rag-smoke")
    args = p.parse_args()
    print(f"tracing: {'on' if tracing_enabled() else 'off'}")
    out = await ainvoke_basic_agent(args.query, thread_id=args.thread_id)
    msg = out["messages"][-1]
    text = getattr(msg, "content", "") or ""
    print(text[:1200])
    if tracing_enabled():
        flush_traces()
    return 0 if text.strip() else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

```bash
.venv/bin/python scripts/lg_rag_smoke.py --query "自动压缩被取消怎么办"
```

---

## S7 · 单测（mock）

要点：mock `ainvoke_evidence_answer`，不连真库 / LLM 也可绿。

```python
import pytest
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.lc_evidence_chain.types import ChainResult


@pytest.mark.asyncio
async def test_basic_agent_appends_ai_message():
    fake = ChainResult(query="q", evidence=[], answer="ok-from-chain", meta={})
    with patch(
        "app.ops.lg_rag.nodes.ainvoke_evidence_answer",
        new=AsyncMock(return_value=fake),
    ):
        from app.ops.lg_rag.graph import build_basic_agent

        graph = build_basic_agent(checkpointer=InMemorySaver())
        out = await graph.ainvoke(
            {"messages": [HumanMessage(content="q")]},
            {"configurable": {"thread_id": "t-test"}},
        )
    last = out["messages"][-1]
    assert isinstance(last, AIMessage)
    assert last.content == "ok-from-chain"
```

```bash
.venv/bin/pytest tests/test_lg_rag_basic.py -q
```

可选加强：同 `thread_id` 连续两次 invoke，断言 `len(messages)` 增长（验证 checkpointer）。

---

## S8 · Golden / 回归（Phase 1 最小解释）

现网 `evals/golden/run_eval.py` 主路径是 **hybrid_recall + grade**，不是完整 `ainvoke_evidence_answer`。Phase 1 不要强行改 runner 语义。

**本期推荐两级**：

| 级别 | 做法 | 用途 |
|---|---|---|
| A · 对齐 | 抽样 N 条 query：直连 LCEL vs `ainvoke_basic_agent`，answer（或规范化后）一致 | 证明「封装无损」 |
| B · 基线 | 沿用既有 R-4 报告作检索基线；全量 73 条「答问通过率」若要做，另开 eval 入口 / 下个 task | 对应总纲 1.6 的产品数字 |

级别 A 示意（脚本或单测均可）：

```python
# 伪代码
direct = await ainvoke_evidence_answer(q)
via_graph = await ainvoke_basic_agent(q, thread_id=f"parity-{i}")
assert via_graph["messages"][-1].content == direct.answer
```

---

## S9 · 图谱与自检

1. 在 `docs/_tech_graph/l1/01_modules.md` 增一行（或扩写）：  
   `lg_rag`：LangGraph 旁路单 Agent（`START→rag→END`）；黑盒复用 `lc_evidence_chain`；**默认不进入** `chat/graph`。  
2. 自检 Chat 图未被改：

```bash
git diff master -- app/ops/chat/graph.py
# 期望：空
```

3. PR 前：`ruff check` 触及文件 · `pytest tests/test_lg_rag_basic.py`。

---

## 明确不做（Phase 1）

| 项 | 原因 |
|---|---|
| Router / 条件边 | Phase 2 |
| rewrite / evaluate 循环 | Phase 3 |
| 挂到 `POST /api/ops/chat/stream` | 避免搅动现网 SSE；旁路 CLI/库级即可 |
| 改 `lc_evidence_chain` 内部拓扑 | 黑盒复用 |
| 改 `chat/graph.py` | 硬约束 |

---

## 未来接回 Chat Graph（本期不做）

旁路稳定且 Golden 对齐后，可另开 task 讨论：

- 将 `rag_node` 作为 Chat 某 intent 的子图；或  
- 共享 checkpointer / tracing 约定  

**不要**在本波改 Chat 边。

---

## 卡点时怎么问 Agent

模板：

```text
阶段：S3
文件：app/ops/lg_rag/graph.py
现象：ainvoke 报错 …
已对照：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md · app/ops/chat/graph.py
请：只辅助改 app/ops/lg_rag/** 与测试/脚本，禁止改 chat/graph.py
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 首版：S0–S9；对齐 PLAN Phase 1 与 LCEL IMPL 体例 |
