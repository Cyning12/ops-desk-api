# Detailed Design：lg_rag Phase 2 · Router Agent（v1 · 待审）

> **总纲**：`docs/guides/PLAN-langgraph-agent-framework_v1.md` Phase 2（第 3 周 · 意图路由）  
> **前置资产**：Phase 1 已完成（`app/ops/lg_rag/`：state / rag_node / graph / checkpointer / tracing）  
> **路线决策**：**2026-08-19 维护者拍板 Track A**——router 落在 `lg_rag` 包演进，**Chat 图继续冻结**；本文含双轨漂移缓解  
> **状态**：draft · 待维护者审；审后走 10-task 建 `task_lg_rag_phase2`，闸前禁改码  
> **硬约束延续**：不改 `app/ops/chat/graph.py`；不改 `lc_evidence_chain` 内部；不挂 SSE

---

## 1. 目标与拓扑

**目标**（PLAN 2.1–2.3）：Agent 自主判断问题类型并分流；闲聊类不再触发 RAG 检索；Golden Set 通过率不降。

```text
START → router_node ─┬─ direct → direct_answer_node → END   # 闲聊/元问题：LLM 直答，不检索
                     ├─ refuse → refuse_node → END          # 越界：固定拒答文案
                     └─ rag → rag_node → END                # 技术问答：Phase 1 黑盒链
```

与 Phase 1 的关系：**并存双图**。`build_basic_agent()`（无 router）保留作回归对照与回滚；新增 `build_router_agent()` 为 Phase 2 主路径。default 切换留到 Phase 2 验收后另议。

---

## 2. State 扩展（PLAN 2.1）

`LgRagState` 增一个字段，**最小扩展**：

```python
class LgRagState(MessagesState):
    route: str  # "rag" | "direct" | "refuse"；router_node 写入；缺省视为 "rag"
```

- PLAN 草案中的 `retrieved_evidence` / `gate_action` / `retry_count` **本波不引入**：evidence/gate 留在 chain 黑盒内部（Phase 1 原则），`retry_count` 属 Phase 3 自纠错。
- TypedDict 语义：新字段无 reducer，节点写回即覆盖；老 checkpoint（无 route 键）读取安全——条件边回调用 `state.get("route") or "rag"`。

## 3. 路由语义与双轨漂移缓解（Track A 配套）

**`route` 与 Chat intent 对齐映射**（语义锚点，防两轨分类口径漂移）：

| Chat intent（规则 · 冻结） | lg_rag route | 说明 |
|---|---|---|
| `issue_qa`（含 #数字） | `rag` | issue 上下文加载能力在 Chat 侧；lg_rag 侧走统一 RAG 链 |
| `general` / `overview` | `rag` | 技术问答主路径 |
| —（Chat 无此分类） | `direct` | 闲聊/元问题（「你是谁」等） |
| —（Chat 由 grade 闸兜底） | `refuse` | 明确越界（求泄密/违法/与运维知识库完全无关且不应答） |

**声明**：`lg_rag` router 为**未来唯一路由真值**；Chat 规则路由（`intent_node`）转入只维护不演进。Phase 3 + golden 达标后另开 task 讨论 lg_rag 接回 Chat 路径（PLAN「未来接回 Chat Graph」节）。

## 4. router_node（PLAN 2.2）

**选型：LLM 分类 + 规则兜底**（PLAN 风险表：LLM 路由不稳定需 fallback）：

1. **规则快路径**：含 `#\d+` → 直接 `rag`（对齐 Chat issue_qa 规则，零成本零误判）。
2. **LLM 分类**：复用 `app.llm.factory` 现有 provider（与 grader 同档小模型），低温度，输出约束为单 JSON `{"route": "rag|direct|refuse"}` + 解析白名单。
3. **fallback**：LLM 异常 / 超时 / 输出非法 → `rag` + warning 日志。**宁检索勿错杀**（技术库产品，错分流到 direct/refuse 的代价高于多检索一次）。

**准确率验收**（PLAN §6：Router 准确率 ≥ 90%）：建小型标注集 `evals/router/labeled_router_v1.yaml`（~30 条：技术 15 / 闲聊 10 / 拒答 5，从真实 query 与构造边界样例取），脚本或 pytest 跑准确率；单测中 LLM 一律 mock。

## 5. direct / refuse 节点

- **direct_answer_node**：LLM 直答闲聊；system prompt 限定 Ops Desk 助手身份、一句话内引回技术主题；不进检索、不读库。
- **refuse_node**：输出固定拒答文案（复用 Chat `REFUSAL_TEXT` 同款常量，避免文案漂移；若 Chat 未导出则在 lg_rag 内定义并在 G-L1 契约备注来源）。

两节点均返回增量 `{"messages": [AIMessage(...)]}`，与 rag_node 同 reducer 语义。

## 6. 观测

- 沿用 `propagate_attributes(trace_name="lg-rag")`（Phase 1 已修命名抢占）；router/direct/refuse 节点经 `trace_span` 进入同一 trace 树。
- router 决策写入 span metadata（route 值、是否 fallback、LLM 原始输出截断），便于准确率排查。

## 7. 测试策略

| 层 | 内容 |
|---|---|
| 单测（mock） | 三路分流各一条；#数字快路径；LLM 异常/非法输出 fallback=rag；老 checkpoint 无 route 键兼容；checkpointer 续写不回归 |
| 标注集 | router 准确率 ≥ 90%（脚本，真 LLM，本地手动） |
| 回归 | 抽样既有 golden 技术问答条目，经 router 图 answer 非空且 route=rag（通过率不降的最小证据；全量 73 仍另开 task） |

## 8. 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| router LLM 异常/超时 | fallback `rag` + warning | Y |
| router 输出非法 JSON/越界值 | 同上 | Y |
| direct_answer LLM 失败 | 异常上抛（与 rag_node 一致语义） | Y |
| 老 checkpoint 无 `route` 键 | 条件边缺省 `rag` | Y |
| 误改 chat/graph 或 chain | 验收打回 | N |

## 9. 实施步骤（30 参考）

1. `state.py`：`LgRagState` 增 `route` 字段。
2. `nodes.py`：`router_node`（规则快路径 + LLM + fallback）、`direct_answer_node`、`refuse_node`、`route_by_route`。
3. `graph.py`：`build_router_agent()` + `ainvoke_router_agent()`（复用 checkpointer/tracing 注入）；basic 保留。
4. `__init__.py` export；smoke 加 `--router`。
5. 标注集 + 准确率脚本；mock 单测。
6. G-L1 `lg_rag` 行备注更新（router 拓扑）+ graph-compile；确认 chat/graph.py 零改动。

## 10. 验收标准（草案，以 task 表为准）

- [ ] 三路分流拓扑生效；闲聊 query 不触发检索（mock 断言 `ainvoke_evidence_answer` 未被调用）
- [ ] `#\d+` 快路径直进 rag；LLM 故障 fallback=rag
- [ ] router 标注集准确率 ≥ 90%
- [ ] `build_basic_agent` 回归不破坏（Phase 1 单测全绿）
- [ ] Langfuse 单 trace 树含 router 节点与 route metadata
- [ ] `git diff master -- app/ops/chat/graph.py` 为空；`lc_evidence_chain` 零改动
- [ ] ruff + pytest 触及路径绿；G-L1 更新 + graph-compile 通过

## 11. 明确不做（Phase 2）

- evaluate / rewrite 循环（Phase 3）；`retry_count`（Phase 3）
- 挂 `POST /api/ops/chat/stream` 或任何 SSE 契约改动
- overview 专用路径（Chat 侧能力；lg_rag 统一走 rag）
- Chat 规则路由的任何改动（冻结）
- 全量 73 条 Golden 回归（另开 task）

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-19 | 首版（AI 起草 · 待审）：Track A 落地——router 入 lg_rag，Chat 冻结；State 最小扩展仅 `route` |
