# task（active）：capability manifest 补 output_fields（planner 契约声明从「猜」变「从清单选」）

> **状态**：active（2026-10-27 维护者签收，00 转录闸表）。
> **由来**：2026-10-27 复跑实证 run `d3a49527929248cc953b7a5327cae2d0`（query「#2140 这个 issue 在说什么？调用write本地落盘结论」）：t1 produces 仍猜 `['title','body','status']`（实际字段 `state`），与钉案 run `cb25483697624aafbb1cf864015c3b10` 同款猜错。已合并的 B 层错误反哺（PR #293）只能事后纠错，且修不动已锁定前缀的声明——源头消灭猜测须另立本 task（PR #293 task 非范围已声明）。
> **分支**：task/lg-rag-capability-output-schema（维护者签收后新建，本窗不建）。

## 根因（已钉案，2026-10-27 双 run 实证）

planner（supervisor）声明 produces/consumes 时，可见信息只有能力 id/描述/入参 schema——`CapabilitySpec`（`app/ops/capability/types.py:72`）**无输出字段声明**，catalog 渲染 `_format_capability_catalog`（`app/ops/lg_rag/multi/nodes.py:1219` 调用点）自然也给不出。模型只能按语义猜（"issue 大概有 status 字段"→ 实际 `state`），猜错空间 100%。

## 修复设计（三层）

1. **契约类型**：`CapabilitySpec` 增 `output_fields: tuple[str, ...] = ()`——声明产出 dict 的字段名清单；**空 = 自由文本/不校验**（承 `step_contract.py:176-185` `output_fields()`「str/list/None 不校验、不替模型猜」既有纪律）。只声明字段名存在性，业务不变量不进 schema（`types.py:3-5` P-16 纪律）。YAML manifest 加载面（`app/ops/capability/manifest.py`）同步支持该键。
2. **真值回填**：`defaults.py` 五能力 + `testing.write.echo`（`manifests/testing.v1.yaml`）填真值；真值以 adapter 实际返回 dict keys 为准（如 `get_issue_by_number` → `number/title/state/html_url/updated_at/labels/body`，`app/ops/capability/lookups.py:69-89`）。
3. **planner prompt 渲染 + 计划期 fail-fast**：catalog 块渲染各能力 output_fields → 声明从「猜」变「从清单选」；声明字段 ∉ 前驱 output_fields（非空时）→ **裁剪该字段 + span/事件留痕**（不拒整 plan、不替模型改语义；裁剪 vs 拒签的口径如 20-audit 有异议，退回维护者裁）。

## 非范围

- 运行期契约闸判定语义与顺序（**task B** `task_lg_rag_gate_produces_unfulfilled.md` 的地盘，互为姊妹 task）。
- 前缀不可变语义；critic/预算策略。
- MCP/http kind 能力的远端输出 schema 自动抓取（output_fields 一律手工声明，空即退回现状）。
- 不动 `args_schema` 与既有任何 CapabilitySpec 字段语义。

## 验收标准

- [ ] 1. 单测：catalog prompt 块含各能力 output_fields 清单；**未声明（空）能力所在行的渲染与现状逐字节一致**（零 diff 口径只在未声明能力上成立）。
- [ ] 2. 单测：声明 produces/consumes 含清单外字段 → 裁剪 + 留痕断言；全在清单内 → 原样通过零 diff。
- [ ] 3. 防漂移钉：测试直接调 adapter 对拍 `get_issue_by_number` 等 output_fields == 实际返回 keys（声明腐化即红）。
- [ ] 4. `.venv/bin/ruff check app tests` 绿（钉版 0.15.21）；`pytest tests` 不引入新红（既有 28 红基线口径，承 PR #293 维护者裁决）。
- [ ] 5. 40 live：复跑 d3a49 场景（#2140 query），t1 produces 收敛为真实字段、t2 write 实际执行成功（LLM 弹性项，失败须附 run 事件链分析）。

## failure_paths

- YAML/默认值声明与 adapter 实际返回漂移 → 验收 3 对拍测试拦截；运行期闸 + B 层 detail 清单（PR #293）仍是最终防线。
- MCP/远端能力无法静态声明 → 空 = 不校验，退回现状（猜 + 事后反哺），不退化。
- catalog prompt 变长 → token 成本；仅字段名清单，量级可控，不留长 description。

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-capability-output-schema` |
| **git_branch** | `task/lg-rag-capability-output-schema` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测（渲染/裁剪/对拍防漂移）+ 40 live 复跑 d3a49 场景；不连真网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a（留痕复用既有 span/事件通道，不新增事件类型）` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default` |
| **close_pr_policy** | `required` |

### 自检结论

结构对齐本仓已合并先例（task_supervisor_replan_error_feedback · PR #293）；元信息块预填含 wiki_delta（承 K4/lint-wiki-delta 首红教训）。姊妹 task B（闸语义）互指非范围，两案可独立签收独立分支。

## 人工闸表

| 闸 | 状态 | 备注 |
|---|---|---|
| HG-AUDIT-R1 | approved | 2026-10-27 维护者签收（m00272「签收A，消除猜测」），00 转录 |
| HG-GRAPH-MODULES | n/a | 不动图谱分层 |
