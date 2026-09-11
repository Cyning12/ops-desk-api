# 实现辅助：LangChain Evidence+Answer Chain（v1）

> **与 task 的关系**：本文件 = **30 手写说明书**；范围/闸/验收真值在  
> `docs/tasks/active/task_langchain_evidence_chain.md` 与  
> `docs/spec/lc-evidence-chain/SPEC-langchain-evidence-chain_v1.md`。  
> **读者**：维护者本人按阶段实现。  
> **硬约束**：不要改 `app/ops/chat/graph.py` 的节点与边。

---

## 总览

目标 LCEL 形态（逻辑）：

```
input: {"query": str}
  → retrieve_evidence   # embed + hybrid_recall → evidence[]
  → answer_from_evidence # LLM → answer
output: {"query", "evidence", "answer", "meta"}
```

建议目录：

```
app/ops/lc_evidence_chain/
  __init__.py      # export build_chain, ainvoke_evidence_answer
  types.py         # EvidenceItem TypedDict / dataclass
  retrieve.py      # 召回 → evidence
  answer.py        # prompt + LLM
  chain.py         # LCEL 组装
scripts/lc_evidence_smoke.py
tests/test_lc_evidence_chain.py
```

---



## S0 · 骨架

**目标**：包可 import。

示例 `__init__.py`：

```
"""LangChain LCEL：evidence + answer（并行于 LangGraph，默认不挂 graph）。"""
from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer, build_chain

__all__ = ["build_chain", "ainvoke_evidence_answer"]
```

示例 `types.py`：

```
from __future__ import annotations
from typing import Any, NotRequired, TypedDict

class EvidenceItem(TypedDict):
    source_type: str
    source_id: str
    chunk_index: int
    anchor: str
    snippet: str
    title: NotRequired[str]
    url: NotRequired[str | None]
    relevance: NotRequired[str]

class ChainResult(TypedDict):
    query: str
    evidence: list[EvidenceItem]
    answer: str
    meta: dict[str, Any]
```

**自检**：`python -c "from app.ops.lc_evidence_chain.types import EvidenceItem"`

---



## S1 · 检索 → evidence

**原则**：只调用 `hybrid_recall`，不要手写 SQL。

对齐现网卡片时，可参考 `app/ops/chat/rag_nodes.py` 的 `_to_source` / `_title_of`（可复制小函数到本包，或抽共享；**P0 允许包内复制纯函数**，禁止复制召回 SQL）。

示例 `retrieve.py`（异步；示意）：

```
from __future__ import annotations
import asyncio
from typing import Any

from app.db.session import AsyncSessionLocal
from app.ops.rag.backend import vector_backend
from app.ops.rag.embedder import SentenceTransformerEmbedder
from app.ops.rag.retrieve import RetrievedChunk, hybrid_recall
from app.ops.lc_evidence_chain.types import EvidenceItem

_embedder: SentenceTransformerEmbedder | None = None

def _get_embedder() -> SentenceTransformerEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformerEmbedder()
    return _embedder

def _title_of(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("Title: "):
            return line[len("Title: "):]
    return ""

def chunk_to_evidence(c: RetrievedChunk, *, relevance: str = "unrated") -> EvidenceItem:
    from app.ops.rag.prefix import strip_doc_context_prefix
    meta = c.metadata or {}
    item: EvidenceItem = {
        "source_type": c.source_type,
        "source_id": c.source_id,
        "chunk_index": c.chunk_index,
        "anchor": c.anchor,
        "snippet": strip_doc_context_prefix(c.content)[:400],
        "title": _title_of(c.content),
        "url": meta.get("html_url"),
        "relevance": relevance,
    }
    return item

async def retrieve_evidence(query: str, *, top_n: int = 5) -> dict[str, Any]:
    emb = _get_embedder()
    qvec = (await asyncio.to_thread(emb.embed, [query]))[0]
    async with AsyncSessionLocal() as session:
        chunks = await hybrid_recall(session, query, qvec, k_each=10, top_n=top_n)
    evidence = [chunk_to_evidence(c) for c in chunks]
    return {
        "query": query,
        "evidence": evidence,
        "meta": {
            "backend": vector_backend().value,
            "hit_count": len(evidence),
        },
    }
```

**自检**：在本机 db+qdrant 有语料时，临时 `asyncio.run(retrieve_evidence("自动压缩"))` 看 `hit_count`。

---



## S2 · 依据 → 回答

示例 `answer.py`：

```
from __future__ import annotations
from typing import Any

from app.llm.factory import get_llm_provider
from app.config import settings

def format_evidence_block(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "（无检索依据）"
    lines: list[str] = []
    for i, e in enumerate(evidence, 1):
        title = e.get("title") or e.get("anchor")
        lines.append(f"[{i}] {e.get('source_type')} {e.get('anchor')} · {title}")
        lines.append(e.get("snippet") or "")
        lines.append("")
    return "\n".join(lines)

async def generate_answer(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload["query"]
    evidence = payload.get("evidence") or []
    if not evidence:
        payload["answer"] = "未检索到足够依据，无法给出有根据的回答。"
        return payload

    provider = get_llm_provider()  # 或指定 provider
    model = getattr(settings, "ops_llm_model", None)
    system = (
        "你是 Ops Desk 助手。只根据给定「检索依据」回答用户问题；"
        "回答末尾用「依据：」列出用到的 anchor 编号。"
    )
    user = f"问题：{query}\n\n检索依据：\n{format_evidence_block(evidence)}"
    from app.llm.schema import LlmMessage
    text = await provider.complete(
        [
            LlmMessage(role="system", content=system),
            LlmMessage(role="user", content=user),
        ],
        model=model,
    )
    payload["answer"] = text if isinstance(text, str) else str(text)
    return payload
```

> **注意**：现网 Provider API 为 `complete(messages: Iterable[LlmMessage])`（见 `app/llm/schema.py`）。  
> 流式可对照 `nodes.py` 的 `complete_stream`；本链 P0 用非流式即可。IMPL 允许对照微调，但不要改 graph。

---



## S3 · LCEL 组装

示例 `chain.py`：

```
from __future__ import annotations
from typing import Any

from langchain_core.runnables import RunnableLambda

from app.ops.lc_evidence_chain.answer import generate_answer
from app.ops.lc_evidence_chain.retrieve import retrieve_evidence

async def _retrieve_step(inp: dict[str, Any]) -> dict[str, Any]:
    query = inp["query"] if isinstance(inp, dict) else str(inp)
    return await retrieve_evidence(query)

def build_chain():
    """返回可 ainvoke 的 Runnable。"""
    retrieve = RunnableLambda(_retrieve_step)
    answer = RunnableLambda(generate_answer)
    return retrieve | answer

async def ainvoke_evidence_answer(query: str) -> dict[str, Any]:
    chain = build_chain()
    return await chain.ainvoke({"query": query})
```

**自检**：

```
import asyncio
from app.ops.lc_evidence_chain import ainvoke_evidence_answer
print(asyncio.run(ainvoke_evidence_answer("自动压缩被取消怎么办")))
```

---



## S4 · CLI 冒烟

示例 `scripts/lc_evidence_smoke.py`：

```
#!/usr/bin/env python3
from __future__ import annotations
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ops.lc_evidence_chain import ainvoke_evidence_answer

async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", required=True)
    args = p.parse_args()
    out = await ainvoke_evidence_answer(args.query)
    print(json.dumps(out, ensure_ascii=False, indent=2)[:4000])
    return 0 if out.get("answer") else 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

运行（本机需 DATABASE_URL / 向量后端可用）：

```
.venv/bin/python scripts/lc_evidence_smoke.py --query "自动压缩被取消怎么办"
```

---



## S5 · 单测（mock）

要点：mock `retrieve_evidence` 或更底层 `hybrid_recall` + LLM，不连真库也可绿。

示意：

```
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_chain_returns_evidence_and_answer():
    fake = {
        "query": "q",
        "evidence": [{
            "source_type": "issue",
            "source_id": "2720",
            "chunk_index": 0,
            "anchor": "2720#0",
            "snippet": "auto compaction",
        }],
        "meta": {"backend": "qdrant", "hit_count": 1},
    }
    with patch(
        "app.ops.lc_evidence_chain.chain.retrieve_evidence",
        new=AsyncMock(return_value=fake),
    ), patch(
        "app.ops.lc_evidence_chain.chain.generate_answer",
        new=AsyncMock(side_effect=lambda p: {**p, "answer": "ok"}),
    ):
        from app.ops.lc_evidence_chain import ainvoke_evidence_answer
        out = await ainvoke_evidence_answer("q")
    assert out["answer"] == "ok"
    assert out["evidence"][0]["anchor"] == "2720#0"
```

（patch 路径随你最终 import 结构调整。）

```
.venv/bin/pytest tests/test_lc_evidence_chain.py -q
```

---



## S6 · 图谱与自检

1. 在 `docs/_tech_graph/l1/01_modules.md` 的 `rag` 行或契约表加一句：
  `lc_evidence_chain`：LangChain LCEL 旁路（evidence+answer）；**默认不进入** `chat/graph`。
2. 自检：
  git diff master -- app/ops/chat/graph.py
  # 期望：空，或仅你明确允许的注释
3. 打开 PR 前跑：`ruff check` 触及文件 · 相关 pytest。

---



## 未来接回 Graph（本期不做）

当旁路稳定后，可把 `retrieve_evidence` / `chunk_to_evidence` 提成共享函数，供：

- 现网 `retrieve_node` 复用（减双份逻辑）  
- 或新 node `evidence_answer` 挂条件边

届时另开 task；**不要**在本波改边。

---



## 卡点时怎么问 Agent

模板：

```
阶段：S2
文件：app/ops/lc_evidence_chain/answer.py
现象：provider.chat 报错 …
已对照：app/ops/chat/nodes.py 的调用方式
请：只辅助改本包，禁止改 graph.py
```

---



## 修订


| 日期         | 说明                   |
| ---------- | -------------------- |
| 2026-08-14 | 首版：S0–S6 示例；维护者手写 30 |


