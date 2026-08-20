# LangGraph Agent 初版规划框架

> **日期**：2026-08-17  
> **状态**：初版框架 · **planning only · 未开 task · 禁止本文件驱动 30 改码**  
> **范围**：在现有 RAG / LCEL Evidence Chain 之上，规划 LangGraph Agent 演进路径（单 Agent → 自纠错 → Multi-Agent）  
> **维护**：每个 Phase 开工前另出 Detailed Design；本文件作总纲持续修订

---

## 0. 与仓内现状对齐（落盘备注）

本框架描述的是「Evidence Chain / Agent 能力」的目标演进，**不等同于从零引入 LangGraph**。仓内已有：

| 能力 | 现状真值 | 与本规划关系 |
|---|---|---|
| Chat LangGraph | `app/ops/chat/graph.py`（intent → retrieve → grade → answer） | 已有 Router / RAG 节点骨架；本规划 Phase 1–3 可对照复用或收敛 |
| SSE 流式 | `POST /api/ops/chat/stream` · `graph.astream` | **已上线**；规划中「Phase 2 引入 SSE」应改为「Agent 路径对齐既有 SSE 契约」 |
| LCEL Evidence Chain | `ainvoke_evidence_answer` · `app/ops/lc_evidence_chain/` | Phase 1 优先封装为 `rag_node` 的黑盒资产 |
| 可观测性 | Langfuse（Chat / Evidence Chain tracing task 进行中） | Phase 1 延续；LangSmith 作本地/Golden Set 调试轨 |
| Checkpointer | Chat graph 当前为 `compile()` 无 checkpointer | Phase 1 关键缺口；优先 InMemory → 再 PostgresSaver |

---

## 1. 框架定位

面向已有完整 RAG 基础设施（Qdrant + BGE-M3 + Reranker + Langfuse）的团队，目标是在现有 LCEL RAG 链基础上，平滑演进到 LangGraph Agent 架构，覆盖从单 Agent 到多 Agent 协作的完整路径。

### 设计原则

| 原则 | 说明 |
|---|---|
| 渐进式演进 | 每个阶段可独立交付、独立回滚 |
| 资产复用最大化 | 不推翻现有 RAG 链路，将其作为 Agent 的「重型工具」复用 |
| 观测先行 | Langfuse + LangSmith 双轨可观测性从第一天接入 |
| 持久化优先 | Checkpointer 在 Phase 1 即接入，避免后期改造 |

---

## 2. LangGraph 核心概念速览

进入规划前对齐底层模型（术语以官方为准，见 [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) / [Overview](https://docs.langchain.com/oss/python/langgraph/overview)）：

| 概念 | 英文 | 说明 |
|---|---|---|
| 状态 | **State** | 在节点间流转的共享数据结构（如 `messages`、`current_route`）；节点写回后由 runtime 合并 |
| 节点 | **Node** | 处理 State 的函数，封装具体逻辑（RAG 检索、Query 改写、LLM 调用等） |
| 边 | **Edge** | 连接节点的有向边；分无条件边与条件边（按 State 动态路由） |
| 图 | **Graph** | `StateGraph` 编译后的可执行工作流（`compile()`） |
| 检查点 | **Checkpointer** | 节点执行后保存 State 快照；支撑断点续传、对话短期记忆、故障恢复 |
| 存储 | **Store** | 跨 thread 的长期记忆（用户偏好、事实等）；与 Checkpointer 互补 |

### LangGraph vs LangChain

- **LangChain**：高层 Agent / 集成框架（模型、工具、LCEL 等）。
- **LangGraph**：底层状态图编排与 runtime（持久化、流式、HITL、循环/分支）。
- 自 LangChain v1.0 起，`AgentExecutor` 已弃用；新的 Agent 抽象建立在 LangGraph 之上。
- LangGraph 解决的核心问题：**线性 Chain 难以表达循环、分支、重试、人工干预**。

---

## 3. 架构总览

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LangGraph Agent 架构                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                 可观测性层 (Langfuse + LangSmith)                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │                     持久化层 (PostgresSaver)                          │    │
│  │              thread_id → State 快照（断点续传 + 对话记忆）            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │                    LangGraph Runtime (StateGraph)                    │    │
│  │                                                                      │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │    │
│  │   │  Router  │───▶│   RAG    │───▶│  Grader  │───▶│ Answer   │     │    │
│  │   │  Node    │    │   Node   │    │   Node   │    │   Node   │     │    │
│  │   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐                      │    │
│  │   │ Rewrite  │◀──▶│ Evaluate │    │  Human   │                      │    │
│  │   │   Node   │    │   Node   │    │  in Loop │                      │    │
│  │   └──────────┘    └──────────┘    └──────────┘                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │                     现有 RAG 基础设施（复用）                        │    │
│  │   Qdrant + BGE-M3 + Reranker + LCEL Evidence Chain                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 分阶段开发路线图

### Phase 1：基础单 Agent（第 1–2 周）—— 建立骨架

> **实现说明书**：`docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md`（S0–S9 · 包路径 `app/ops/lg_rag/`）

**目标**：将现有 RAG 链路封装为 LangGraph Node，跑通最小可用 Agent。

| 任务 | 产出 | 验收标准 |
|---|---|---|
| 1.1 安装 `langgraph`、`langgraph-checkpoint-postgres` | 依赖就绪 | 安装成功且与现仓版本兼容 |
| 1.2 将 `ainvoke_evidence_answer` 封装为 `rag_node` | `rag_node` 函数 | 单个 Query 能走通完整 RAG |
| 1.3 构建最小 StateGraph：`entry → rag_node → end` | `build_basic_agent()` | 本地 `ainvoke` 返回正确答案 |
| 1.4 接入 PostgresSaver（可先 InMemorySaver 冒烟） | Checkpointer 就绪 | 服务重启后同一 `thread_id` 能恢复状态 |
| 1.5 接入 Langfuse 回调 | Trace 可见 | Langfuse UI 能看到 Agent 执行树 |
| 1.6 跑通 Golden Set（73 条）回归 | 基线报告 | 通过率 ≥ 当前 RAG 基线（57/73） |

**代码骨架示例**：

```python
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.postgres import PostgresSaver

from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer

# 1. 封装现有 RAG 链为 Node
async def rag_node(state: MessagesState):
    query = state["messages"][-1].content
    result = await ainvoke_evidence_answer(query)
    return {"messages": [AIMessage(content=result.answer)]}

# 2. 构建 Graph + Checkpointer
checkpointer = PostgresSaver.from_conn_string(settings.database_url)
builder = StateGraph(MessagesState)
builder.add_node("rag", rag_node)
builder.set_entry_point("rag")
builder.set_finish_point("rag")
graph = builder.compile(checkpointer=checkpointer)

# 3. 调用（支持断点续传）
config = {"configurable": {"thread_id": "session-123"}}
result = await graph.ainvoke(
    {"messages": [HumanMessage(content=query)]},
    config,
)
```

> **注意**：`PostgresSaver` 的 `thread_id` 建议 ≤ 255 字符；生产表需 `checkpointer.setup()`（或等价迁移），否则易踩「表未创建」坑。

---

### Phase 2：Router Agent（第 3 周）—— 意图路由

**目标**：Agent 自主判断问题类型，分流到不同处理路径。

| 任务 | 产出 | 验收标准 |
|---|---|---|
| 2.1 设计 State 扩展（`route`、`should_retrieve` 等） | 自定义 State | TypedDict / Pydantic 定义完成 |
| 2.2 实现 `router_node`（闲聊 / 技术问答 / 拒答） | Router 逻辑 | 闲聊类不再触发 RAG 检索 |
| 2.3 条件边：按 `route` 分流到 `rag_node` / `direct_answer_node` / `refuse_node` | 条件路由 | Golden Set 通过率不降 |

**State 设计草案**：

```python
from typing import TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: list[BaseMessage]           # 对话历史
    route: str                            # "rag" | "direct" | "refuse"
    retrieved_evidence: list[EvidenceItem]  # RAG 检索结果
    gate_action: str | None               # "answer" | "answer_partial" | "refuse"
    retry_count: int                      # 重试次数
```

> **现状对照**：Chat 路径已有 `detect_intent` + 条件边；本 Phase 若落在 Evidence Agent，应明确是「新建 Agent 图」还是「与 Chat graph 收敛」，避免双轨路由逻辑漂移。

---

### Phase 3：自我纠正机制（第 4–5 周）—— 自纠错

**目标**：评估检索质量；不佳时自动 Query 改写并重试。

| 任务 | 产出 | 验收标准 |
|---|---|---|
| 3.1 实现 `evaluate_node`（复用现有 Grader，判 evidence 质量） | 评估节点 | 输出 `quality: high / medium / low` |
| 3.2 实现 `rewrite_node`（LLM 同义改写 Query） | 改写节点 | 改写后语义不变 |
| 3.3 条件边：`quality=low` → `rewrite_node` → `rag_node`（最多 2 次） | 循环重试 | G37、G39 等漏召回 Case 至少改善 3 条 |
| 3.4 `max_retries` 熔断 | 防死循环 | 超过 2 次直接拒答 |

**流程图**：

```text
用户 Query → router_node
    │
    ├── direct → direct_answer_node → END
    │
    └── rag → rag_node → evaluate_node
                              │
              ┌───────────────┼───────────────┐
              │               │               │
           quality=high   quality=medium  quality=low
              │               │               │
           answer_node    answer_node    rewrite_node
              │               │               │
              └───────────────┴───────┬───────┘
                                      │
                         retry_count < max_retries (2)
                                      │
                                      ▼
                               rag_node（重试）
```

---

### Phase 4：Multi-Agent（第 6–8 周）—— 多智能体协作

**目标**：引入 Supervisor 模式，多个专业 Agent 协作完成复杂任务。

| 任务 | 产出 | 验收标准 |
|---|---|---|
| 4.1 设计 Supervisor 节点（任务拆解 + 分配） | Supervisor 逻辑 | 能识别复合问题并拆解子任务 |
| 4.2 将 RAG Agent 封装为 SubGraph | 可复用子图 | 可独立运行、可被 Supervisor 调用 |
| 4.3 增加 InfoExtract Agent（日期 / 版本号 / 人名等） | 信息抽取 | 能从文本结构化抽取实体 |
| 4.4 增加 Tool Executor Agent（外部 API，可先 Mock） | 工具执行器 | 能调用 Mock API 返回结果 |
| 4.5 实现 Aggregator 节点 | 综合报告 | 输出含多源信息的结构化答案 |

**多智能体架构**：

```text
                         ┌─────────────────┐
                         │   Supervisor    │
                         │   （任务拆解）   │
                         └────────┬────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
          ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
          │  RAG Agent  │ │ InfoExtract │ │  Tool Exec  │
          │  (SubGraph) │ │   Agent     │ │   Agent     │
          └─────────────┘ └─────────────┘ └─────────────┘
                 │                │                │
                 └────────────────┼────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Aggregator     │
                         │  （结果合并）    │
                         └─────────────────┘
```

---

## 5. 技术决策记录（ADR 摘要）

| 决策点 | 选择 | 理由 |
|---|---|---|
| Checkpointer | `PostgresSaver` | 复用现有 PostgreSQL；2C4G 下不引入 Redis 新组件 |
| 可观测性 | Langfuse（生产）+ LangSmith（调试） | 生产流量挂 Langfuse；Golden Set / 本地调试用 LangSmith |
| RAG 集成方式 | 整体封装为 Node | 避免拆散 Retrieve/Grade/Answer，保持黑盒复用 |
| State 设计 | 继承 / 扩展 `MessagesState` | 与 LangChain 消息格式兼容 |
| 流式传输 | **对齐现有 Chat SSE**（非「从零引入」） | 降低感知延迟；思考过程可视化；契约复用 `stream` 事件 |

---

## 6. 实施计划与风险

| 阶段 | 时间 | 关键里程碑 | 主要风险 |
|---|---|---|---|
| Phase 1 | 第 1–2 周 | Golden Set 回归通过 | Checkpointer 表需 `setup()` / 迁移；与现 Chat graph 双轨并存 |
| Phase 2 | 第 3 周 | Router 准确率 ≥ 90% | LLM 路由不稳定，需 fallback；与 Chat `detect_intent` 策略可能冲突 |
| Phase 3 | 第 4–5 周 | 漏召回改善 ≥ 3 条 | 循环重试导致延迟飙升 → 必须熔断 |
| Phase 4 | 第 6–8 周 | 复合问题综合报告 | Multi-Agent 协调开销大，需压测 |

### 立即行动（本周，仍须先开 task + 人工闸后再改码）

1. 确认 `langgraph` / `langgraph-checkpoint-postgres` 与现仓依赖版本矩阵。
2. 将 `ainvoke_evidence_answer` 封装为 `rag_node`（设计级草案即可）。
3. 本地跑通最小 StateGraph + `InMemorySaver`（先不接 PG）。
4. 确认 Langfuse Callback 在 LangGraph 路径能正确捕获 Trace。

---

## 7. 扩展预留接口

| 扩展点 | 预留方式 | 未来用途 |
|---|---|---|
| 长期记忆 | State 预留 `user_profile`；或接入 LangGraph **Store** | 跨会话用户画像（可落 Qdrant） |
| Human-in-the-loop | 条件边预留 `pending_approval`；官方 **interrupt** | 敏感操作前中断等待人工确认 |
| 工具生态 | Node 统一 `async def node(state) -> dict` | 新增工具 Node 即插即用 |
| 流式输出 | `stream_mode="messages"` / 对齐现有 SSE | Agent 路径接入既有前端契约 |

---

## 8. 参考资料

| 主题 | 链接 |
|---|---|
| Graph API 概述 | https://docs.langchain.com/oss/python/langgraph/graph-api |
| Persistence / Checkpointer | https://docs.langchain.com/oss/python/langgraph/persistence |
| LangGraph Overview | https://docs.langchain.com/oss/python/langgraph/overview |
| Thinking in LangGraph | https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph |
| Functional API | https://docs.langchain.com/oss/python/langgraph/functional-api |
| Human-in-the-loop / Interrupts | https://docs.langchain.com/oss/python/langgraph/interrupts |
| 开源教程（系统化学习） | https://github.com/ShadowQuill/langchain-langgraph-tutorial |

---

## 9. 文档状态

- **当前**：初版框架（总纲）。
- **下一步**：Phase 开工前独立 Detailed Design（含与 `app/ops/chat/graph.py` 的收敛/并存决策）。
- **改码门槛**：须先有 `docs/tasks/active/task_*.md`，且 `HG-AUDIT-R1` 等人工闸 `approved` 后方可 30。
