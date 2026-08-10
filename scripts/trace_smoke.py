#!/usr/bin/env python3
"""Langfuse 埋点冒烟：直连 graph 跑一次 chat（绕过 HTTP/鉴权），验证 trace 上报。

前置：.env 配好 LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL
      且 OPS_CHAT_TRACER=langfuse。
注意：dotenv 必须在任何 langfuse import 之前加载（SDK 初始化读 os.environ）。
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
from app.ops.tracing import flush_traces, tracing_enabled  # noqa: E402


async def main() -> int:
    print(f"tracing_enabled: {tracing_enabled()}")
    state: ChatState = {
        "query": "issue #2720 是什么原因导致自动压缩被取消？",
        "session_id": "trace-smoke",
        "model": None,
    }
    async for event in run_chat_stream(state):
        et = event.get("event_type")
        if et in ("tool_result", "error", "model.fallback"):
            print(et, "→", str(event.get("payload"))[:120])
    flush_traces()
    print("done. 到 Langfuse UI Traces 视图确认 trace 'ops-chat'")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
