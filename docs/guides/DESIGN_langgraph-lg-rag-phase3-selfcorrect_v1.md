# Detailed Design：lg_rag Phase 3 · 自我纠正（evaluate/rewrite 循环）（v1 · 待审）

> **总纲**：`docs/guides/PLAN-langgraph-agent-framework_v1.md` Phase 3（第 4–5 周 · 自纠错）  
> **前置资产**：Phase 1（basic 图 / checkpointer / tracing）· Phase 2（router 三路，标注集 100%）  
> **状态**：**approved（2026-08-21 维护者会话签收）**；task=`docs/tasks/active/task_lg_rag_phase3.md`  
> **硬约束延续**：不改 `app/ops/chat/graph.py`；不改 `lc_evidence_chain` 内部；不挂 SSE  
> **关键事实**：chain 黑盒输出 `ChainResult.meta` 已含质量信号（`gate_action` / `hit_count` / `kept_count` / `best_relevance` / `grade_count`，见 chain.py `_meta_span_update`）——evaluate 无需第二次 grader LLM

---

## 1. 目标与拓扑

**目标**（PLAN 3.1–3.4）：评估检索质量，不佳时自动改写 Query 重试，最多 2 次熔断；G37、G39 等漏召回 case 改善 ≥3 条。

```text
START → router ─┬─ direct → direct_answer → END
                ├─ refuse → refuse → END
                └─ rag → rag_node → evaluate_node
                                       ├─ high   → END
                                       ├─ medium → END（部分证据可答，不重试）
                                       └─ low ─── retry_count < 2 → rewrite_node ─→ rag_node（回环）
                                                  retry_count ≥ 2 → END（熔断，保留末次答案）
```

只改 router 图；basic 图继续冻结作对照。

## 2. State 扩展（PLAN 草案字段的本波取舍）

```python
class LgRagState(MessagesState):
    route: str                     # Phase 2
    retry_count: int               # Phase 3：rewrite_node 递增；缺省 0
    current_query: str             # Phase 3：rewrite 后的查询；rag_node 优先取用
    chain_meta: dict               # Phase 3：ChainResult.meta 质量信号子集（evaluate 数据源）
```

- `chain_meta` 只存 `gate_action/hit_count/kept_count/best_relevance/grade_count` 五个标量；**evidence 本体不进 state**（黑盒原则 + checkpoint 体积）。
- PLAN 草案的 `retrieved_evidence` 本波以 `chain_meta` 轻量替代；`gate_action` 以 `chain_meta["gate_action"]` 承载。
- 老 checkpoint 兼容：三字段缺省（`retry_count=0`、`current_query` 缺失回退末条 HumanMessage、`chain_meta` 缺失视为 high 不重试——安全默认防意外回环）。

## 3. evaluate_node（PLAN 3.1 · 复用现有 Grader 结论）

**确定性映射，不调 LLM**——chain 内部 grader 已判过证据质量，gate 即其结论：

| 条件（按序） | quality | 去向 |
|---|---|---|
| `chain_meta` 缺失 / `gate_action=="answer"` | high | END |
| `gate_action=="answer_partial"` | medium | END（有证据但部分；重写收益不确定、延迟翻倍，对齐 PLAN 流程图 medium→answer） |
| `gate_action=="refuse"` 或 `kept_count==0` | low | `retry_count<2`→rewrite；否则 END（熔断） |

## 4. rewrite_node（PLAN 3.2）

- LLM 改写（与 router 同档小模型、低温度）：输入 `current_query or 末条 HumanMessage`。**2026-08-21 实施修正（30 中发现）**：长句自然语言 query 会被检索层零命中（实测：`readPullRequest` 单词命中 issue 87，G37 整句 0 命中），故 prompt 从「同义改写」改为「**核心可检索关键词组合**」（保留函数名/错误码/组件名，去叙述包裹，可中英混合），输出单行关键词。
  - 针对 G37/G39 这类**复合机制问**：引导展开关键侧面而非拆成多查询（rag_node 是单查询入口；多查询并行检索属非范围）。
- 写回 `current_query` + `retry_count += 1`；写 span metadata（原/新 query 截断、retry_count）。
- **熔断语义**：LLM 失败 / 输出为空 / 与原 query 相同 → 不写回、不递增，直接 END（视为无法改写，终止回环）。
- `max_retries=2`（env `LG_RAG_MAX_RETRIES` 可覆盖；PLAN 3.4）。

## 5. rag_node 修改（最小侵入）

```python
query = state.get("current_query") or _last_user_text(state["messages"])
result = await ainvoke_evidence_answer(query)
return {
    "messages": [AIMessage(content=result.answer or "")],
    "chain_meta": {k: result.meta.get(k) for k in _META_KEYS if k in result.meta},
}
```

- 无 `current_query` 时行为与 Phase 1/2 完全一致（回归保障）。
- **中间答案留存**：每次尝试都追加 AIMessage（含可能的拒答文案），末条即最终答案——保留尝试轨迹利于观测；SSE 接入时再收敛呈现。

## 6. 观测

- evaluate / rewrite 进 `trace_span`；decision metadata：`quality`、`retry_count`、`chain_meta` 子集、改写前后 query 截断。
- Langfuse 单树可见回环次数（router → rag → evaluate → rewrite → rag …）。

## 7. 测试策略

| 层 | 内容 |
|---|---|
| mock 单测 | evaluate 三路映射；low→rewrite→rag 回环一次后 high；连续 low 达 2 次熔断（rewrite 恰好 2 次）；rewrite LLM 失败→END 不回环；rag_node 用 `current_query`（chain 收到改后 query）；`chain_meta` 写回；老 checkpoint 兼容；Phase 1/2 单测不回归 |
| 漏召回改善（PLAN 3.3 · 真 LLM+库手动） | `scripts/lg_rag_retry_eval.py`：候选池 = `evals/golden/queries_v1.yaml` 中 `expect_relevance: weak` / 历史 miss 条目（含 G37/G39），对比 basic 一次检索 vs router+retry 图的 `gate_action`/`kept_count`；**改善定义**：refuse 或 kept=0 → answer/answer_partial 或 kept>0；验收 ≥3 条，结果记 task |
| 回归 | Phase 2 标注集准确率不回归（router 未动，预期不变，抽查即可） |

## 8. 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| rewrite LLM 失败/空/同文 | 直接 END（不回环、不递增） | Y |
| rag 重试仍 low | 达 2 次熔断 END，保留末次答案 | Y |
| `chain_meta` 缺失 | 视为 high，不回环 | Y |
| 改写引入语义漂移 | 标注集/漏召回 eval 观测；prompt 已约束 | — |
| 误改 chain / chat 图 | 验收打回 | N |

## 9. 实施步骤（30 参考）

1. `state.py`：增 `retry_count` / `current_query` / `chain_meta`。
2. `nodes.py`：`evaluate_node` / `route_by_quality` / `rewrite_node`；`rag_node` 改取 `current_query` + 写回 `chain_meta`。
3. `graph.py`：router 图加 evaluate/rewrite 节点与回环条件边。
4. mock 单测；`scripts/lg_rag_retry_eval.py` 实跑漏召回候选池。
5. G-L1 备注更新 + graph-compile；确认 chat/chain 零改动。

## 10. 验收标准（草案，以 task 表为准）

- [ ] low→rewrite→rag 回环生效；最多 2 次熔断（mock 断言调用次数）
- [ ] rag_node 重试时使用改写后 query（mock 断言 chain 入参）
- [ ] G37、G39 等漏召回 case 改善 ≥3 条（retry_eval 实跑结果记 task）
- [ ] Phase 1/2 全部单测不回归；ruff 绿
- [ ] Langfuse 单树可见回环与 quality/retry metadata
- [ ] `git diff master`：chat/graph.py 与 lc_evidence_chain 零改动

## 11. 明确不做（Phase 3）

- 多查询分解并行检索（单查询改写优先；需要时另议）
- `retrieved_evidence` 进 state（`chain_meta` 轻量替代）
- SSE / Chat 接入；Chat 图任何改动
- 全量 73 条 Golden 回归（仍另开 task）
- Multi-Agent（Phase 4）

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-21 | 首版（AI 起草 · 待审）：evaluate 复用 chain gate 结论（零额外 LLM）；rewrite 单查询改写 + 2 次熔断；state 增 3 字段 |
| 2026-08-21 | 维护者会话签收，无修订；转入 30 |
| 2026-08-21 | 30 实施修正：rewrite 策略改关键词组合（G37 诊断驱动）；router prompt 收紧 direct 定义（eval 发现「有没有某功能」类误分流 direct），标注集扩至 34 条复测 100% |
