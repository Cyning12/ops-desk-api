# Session · 域夹（L1）

> **track**：`agent-infra` / session  
> **规划轨**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md) 波次 **H3**  
> **实现落点**：`app/ops/chat/` · `app/db/` · 可选 `app/ops/session/`

---

## 本夹文件

| 文件 | 说明 |
|---|---|
| [`ROADMAP_chat_continuity_v0.md`](./ROADMAP_chat_continuity_v0.md) | H3：多轮、压缩、SSE 断点 |

**边界**：不动 `chat/graph.py` 拓扑；会话与流传输衔接属本域。
