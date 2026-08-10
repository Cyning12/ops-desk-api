#!/usr/bin/env python3
"""R-3 检索链冒烟：不带 #n 的问题走 retrieve → grade → gate → answer 全程。

前置：.env 配好 LLM/Bailian/Langfuse 环境；bge-m3 本地快照已缓存。
用法：.venv/bin/python scripts/rag_smoke.py ["自定义问题"]
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()  # 必须先于 langfuse 相关 import

from app.ops.chat.service import run_chat_stream  # noqa: E402
from app.ops.chat.state import ChatState  # noqa: E402
from app.ops.tracing import flush_traces  # noqa: E402

G01 = "Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因?"


async def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else G01
    state: ChatState = {"query": query, "session_id": "rag-smoke", "model": None}
    answer_parts: list[str] = []
    async for event in run_chat_stream(state):
        et = event.get("event_type")
        payload = event.get("payload", {})
        if et == "tool_result":
            if payload.get("tool") == "retrieve":
                print("retrieve →", payload.get("hits"))
            elif payload.get("tool") == "grade":
                print("grade →", payload.get("gate_action"),
                      [(g["relevance"]) for g in payload.get("grades", [])])
                for s in payload.get("sources", []):
                    print(f"  source: {s['anchor']} · {s['relevance']} · {s['title'][:40]}")
        elif et == "answer":
            answer_parts.append(payload.get("content", ""))
        elif et == "error":
            print("error →", payload)
    flush_traces()
    print("\n== 答案 ==\n" + "".join(answer_parts)[:600])
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
