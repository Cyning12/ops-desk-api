# ROADMAP：Strategy Builder · Intent · 再赋能闭环（L0）

> **层级**：L0 Host 下一轨规划（跨 orchestration / capability / skill / prompt）  
> **状态**：`active`（规划真值 · HG-SPEC-SIGNOFF **approved** · 2026-08-27；**不**直接授权 30；须另开 task + 人工闸）  
> **上游**：[`02_agent_host_plan_v0.md`](./02_agent_host_plan_v0.md)（H1–H5 **CLOSE**）· [`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md)  
> **域夹**：[`strategy/`](./strategy/)  
> **讨论来源**：2026-08-27 会话（H1 闭环解读 → Strategy Builder / Intent / YAML 目录 / Critic 再赋能）  
> **首棒实现**：[`task_strategy_builder_allowlist`](../../tasks/done/task_strategy_builder_allowlist.md)（S1 · #78 MERGED）  
> **次棒实现**：[`task_intent_schema_v1`](../../tasks/done/task_intent_schema_v1.md)（S2 · #80 MERGED）  
> **三棒实现**：[`task_catalog_manifest_yaml`](../../tasks/done/task_catalog_manifest_yaml.md)（S3 · 00 验收 PASS）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **plan_slug** | `strategy-and-intent` |
| **invoke_slug** | `catalog-manifest-yaml`（S3 进行中；S2 `intent-schema-v1` #80 MERGED） |
| **test_strategy** | `required`（按子波次裁剪；S3 fixture YAML/JSON） |
| **graph_change_layer（建议）** | 多为 `G-L1`（`capability` 备注；**不**默认新增一级模块） |
| **默认分支** | `task/catalog-manifest-yaml` |

### 人工闸（SPEC / S0）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 2026-08-27 · **00 代签 · 维护者 Prompt 授权**（`PROMPT_00_strategy-builder-s1`） |

---

## 1. 背景：H1–H5 收官后仍缺什么

Agent Host flesh（H1–H5）已交付基建，**不等于**「意图 → 赋能策略 → 工作 supervisor → 质量闭环」形态。

| 波次 | 交付 | 相对目标形态 |
|---|---|---|
| H1 | supervisor 读 `list_capabilities` + tool id Host 校验 | 仅有**工作 planner**；可见集仍由代码 filter 写死 |
| H2 | invoke 前 Policy 门 | **执行闸**，非按意图裁本轮可见集 |
| H3 | Chat 会话连续性 | 正交 |
| H4 | PromptAssembly | 模板装配，非策略构建 |
| H5 | Skill 索引 + NL match → `provide` | 可作 Builder **输入**；非全量赋能 + 再绑定 |

**缺口（本轨）**：

1. **Strategy Builder**：按意图/策略写出本轮可见 capability/skill 白名单（写入 state）  
2. **Intent 升级**：比现 `router` 三路（`rag|direct|refuse`）更细的结构化意图  
3. **Critic / 再赋能**：结果未达标时，同 catalog 重试 vs 回 Builder 换赋能  
4. **目录配置化**：全量能力可由 YAML/manifest 动态加载注册（Host 权威）

---

## 2. 目标形态（Mode A 兼容）

```text
Query
  → ① 粗路由闸（可选保留 router：rag|direct|refuse）
  → ② Intent（LLM + Structured Output · 丰富 schema）
  → ③ Strategy Builder
        输入：Registry 全量视图 + Policy + Intent +（可选）Skill match
        输出：state.allowed_capability_ids / skill_ids / 预算与重试策略
  → ④ Work Planner（现 supervisor_node）
        只读已赋能可见集 → 拆 subtasks plan
  → ⑤ Workers（rag / extract / tool_exec / provide）
  → ⑥ Critic / Aggregator
        达标 → END
        执行质量差 → 回 ④（同 catalog）
        能力缺口 → 回 ③（rebind · 扩/换可见集）
        意图错 → 回 ②→③
```

硬约束（继承 `00` / `02`）：

- **静态图 + 动态 plan / 动态可见集**；禁止每请求 `compile` 新图  
- Builder **不得**绕过 Policy；不得由模型随意 `register` 高危能力  
- Host 校验（SO / allowlist / Policy）不可做成模型可选 tool  
- Mode A：`list_capabilities` + `invoke` / `provide`

---

## 3. 命名边界（钉死）

| 名称 | 职责 | 不是什么 |
|---|---|---|
| **Strategy Builder** | 本轮策略：意图摘要消费 + 可见集裁剪 +（可选）重试/预算写入 state | 「权限更大的 supervisor」；不是 Policy 本身 |
| **Policy（H2）** | Host 硬闸：高危默认拒、sandbox/cli env；键仅 Host | 不可由 Builder LLM 改写 |
| **Work Planner / `supervisor_node`** | 在已赋能范围内拆 plan、选 tool/skill id | 不负责决定「本轮能看见哪些能力」 |
| **Catalog / Registry** | 进程内能力真值；可由 YAML 启动/热加载注册 | Builder 运行时随意增删 |
| **Skill match（H5）** | NL → skill_id 候选 → provide | 完整 Skill 引擎；不等于 Strategy Builder |

产品名：**Strategy Builder**。包/模块建议：`app/ops/strategy/` 或 `catalog_binder`（00 定夺）；对外文档统一 Strategy Builder。

---

## 4. 失败分流（Critic）

| 失败类型 | 优先策略 | 回环 |
|---|---|---|
| 参数/表述/抽取不全 | 同可见集内重 plan 或 worker 短观察 | → ④ |
| plan 非法 / tool 幻觉 | 现有 fallback 或 ④ 重拆 | → ④ |
| 能力不足（缺 MCP/skill/档位） | **换赋能** | → ③ |
| 意图判错 | 重意图再赋能 | → ②→③ |
| 预算耗尽仍不达标 | 升人类 / 安全降级 END | Host 闸 |

原则：**先窄后宽**（同 catalog → rebind）；`max_inner_retries` + `max_rebinding`；span：`rebinding_count` / `react_attempt` / `strategy_builder_*`。

全图自由 ReAct **非默认**；优先结构化 plan + 条件边回环。Worker 内短观察→再 invoke 可试点。

---

## 5. Intent 升级立场

- 现 `router_node`：已是 LLM，但契约粗、prompt **业务强耦合**（运维知识库三路）。  
- 升级方向：更丰富的 **Intent schema**（域、需否 tool/skill、风险档、是否复合任务）→ 喂给 Strategy Builder。  
- 粗 `router` 可保留为**外层安全闸**；细意图另节点，避免一个 prompt 兼做安全三路与策略输入。  
- 「更灵活靠一层 LLM」：**对**，但是 **LLM + SO Host 校验**，不是自由对话替代枚举。

---

## 6. 全量能力动态加载

| 做法 | 态度 |
|---|---|
| YAML/JSON manifest（id · kind · description · tags · risk · enabled · adapter 指针） | **推荐** |
| 启动或受控热加载 → Host `register` / 更新 Registry | **允许** |
| Builder 只读 `list_capabilities` 或同一 manifest 逻辑全量再裁剪 | **主路径** |
| Builder LLM 直接改 Registry / 绕过 Policy | **禁止** |

YAML 管**元数据与注册清单**；执行仍走 adapter。热更新须版本号 + 观测，避免请求中途目录突变。

默认 defaults（`app/ops/capability/defaults.py`）可逐步迁为「内置 manifest」或与 YAML 并存。

---

## 7. 建议波次（可拆 task）

| 序 | ID | 摘要 | 依赖 |
|---|---|---|---|
| **S0** | `strategy-spec-signoff` | 本文件 + `strategy/ROADMAP` 维护者签收 | — |
| **S1** | `strategy-builder-allowlist` | state 白名单；supervisor ∩ allowlist；规则/配置 Builder（可无 LLM） | H1 ✓ |
| **S2** | `intent-schema-v1` | 细 Intent schema + 节点；与粗 router 并存策略 | S1 · H4 |
| **S3** | `catalog-manifest-yaml` | manifest 加载注册；与 defaults 迁移策略 | S1 |
| **S4** | `critic-rebind` | Critic 节点 + 同 catalog / rebind 条件边 + 预算 | S1–S2 |

详规：[`strategy/ROADMAP_strategy_builder_v0.md`](./strategy/ROADMAP_strategy_builder_v0.md)。

**禁止**：未过 S0/S1 先上无预算的全图 ReAct 或让模型自改 Policy。

---

## 8. 与现资产对照

| 资产 | 关系 |
|---|---|
| `supervisor_node` + `_SUPERVISOR_CAP_FILTER` | S1 起改为「filter ∩ state allowlist」 |
| `capability.policy` | 始终在 invoke 路径；Builder 输出不得覆盖 Host 键 |
| SkillRegistry / `match_skills` | Builder 可选输入；匹配结果进 allowlist 或 provide slot |
| PromptAssembly | Builder / Intent 的 system 模板走 H4 槽位 |
| `lg_rag` router 图 | 与 supervisor 图并存；S2 定「意图节点挂哪张图」 |

---

## 9. 非目标

- A2A / 每请求动态 compile 新图  
- 完整 Skill 执行引擎  
- 用 Strategy Builder 替代 Policy  
- 默认改 `chat/graph.py` 拓扑（首批仍优先 `lg_rag`）

---

## 10. 00 入口（草案）

- 域 ROADMAP：[`strategy/ROADMAP_strategy_builder_v0.md`](./strategy/ROADMAP_strategy_builder_v0.md)  
- 签收后：拆 `docs/tasks/active/task_*.md`（建议首棒 `strategy-builder-allowlist`）  
- **本文件不授权 30 改码**

---

## 11. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版：会话结论整合（H5 后缺口 · Strategy Builder 命名 · Intent · YAML · Critic 分流） |
| 2026-08-27 | 交叉引用测评轨 [`04_eval_and_observability_plan_v0.md`](./04_eval_and_observability_plan_v0.md)（Critic/准确率与 Eval 正交） |
| 2026-08-27 | **HG-SPEC-SIGNOFF=approved**（S0 · 00 代签 · 维护者 Prompt 授权）；状态 `active`；拆 S1 `strategy-builder-allowlist` |
| 2026-08-27 | S1 allowlist 00 验收 PASS；[#78](https://github.com/Cyning12/ops-desk-api/pull/78) **MERGED** |
| 2026-08-27 | S2 Intent 00 验收 PASS；[#80](https://github.com/Cyning12/ops-desk-api/pull/80) **MERGED** |
| 2026-08-28 | S3 catalog manifest 00 验收 PASS |
