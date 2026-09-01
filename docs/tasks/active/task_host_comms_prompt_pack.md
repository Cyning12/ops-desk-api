# Task：Host C2 · comms Prompt Pack（PromptAssembly pack=comms）

> **状态**：active  
> **类型**：Prompt 工程 / Host 沟通轨实现  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](../../spec/agent-infra/06_host_comms_boundary_spec_v0.md)（**signed** · #111）§4（意图路由）· §5（产物路径）· §6（闸纪律）· §9（session 隔离）· §10（C2 行）  
> **前置**：C1 CLOSE · [`task_host_harness_cli_capability`](../done/task_host_harness_cli_capability.md) · [#114](https://github.com/Cyning12/ops-desk-api/pull/114)；H4 方向 ✓ · kit ≥1.10 FRAGMENT 已 sync 仓内（`docs/harness/prompts/FRAGMENT_00_delegate_only_v1_zh.md` · `FRAGMENT_hat_reanchor_v1_zh.md`）  
> **分支**：`task/host-comms-prompt-pack`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **无关**：C1 已完成项返工 · C3 受控写盘 · C4 UI · 改 product pack / 业务 Chat·lg-rag 行为 · 新增 HTTP 路由 · 真 LLM 联调

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `host-comms-prompt-pack` |
| **git_branch** | `task/host-comms-prompt-pack` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 纯函数单测：pack 渲染槽位填充断言（FRAGMENT 内容注入 · task 字段清单 · 禁令条文）；意图路由判定器参数化用例（立项关键词→comms · 默认→product · 误判回退）；product/comms system 不混断言；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（**10 已核现网钉**：prompt 装配层 `app/ops/prompts/**` 归属 `lg_rag` 行 L27——现网模板 id 全部 `lg_rag.*` 前缀且被 lg_rag supervisor/intent 消费；仅该行备注，不新增一级模块） |
| **graph_delta_note** | 不新增一级模块；prompts 属既有模块则仅备注；若增 `implementedBy` → 同步 G-L2 indexes |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 SPEC 06 §4/§9 + 本 task；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `n/a`（不改 lg-rag-sse-v1；pack 契约由本 task 30 自检记录） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C 轨串行：C0 ✓ → C1 ✓ → **C2** → C3；C4 跨仓 web 可后与 C3 尾并行 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | pending | 30 | 待 **20-task-audit** R1 落盘后 00 代签 |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** · 仅备注 |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`host-comms-prompt-pack`** |
| **交付形态** | **纯函数层**：`app/ops/prompts/` 扩展 pack 概念（如 `packs.py`：`render_pack("comms", slots)` → system/messages）+ 意图路由判定器 `route_intent(text)` → `"comms" \| "product"`。**不新增 HTTP 路由**（接线留 C3/C4 或另议） |
| **槽位链** | system 短层 = 仓内 kit FRAGMENT 真值文件（`docs/harness/prompts/FRAGMENT_00_delegate_only_v1_zh.md` + `FRAGMENT_hat_reanchor_v1_zh.md` · 运行时读文件或构建期内嵌由 30 定 · 但禁止拷贝后漂移失同步）+ task 模板字段清单（slug/范围/非范围/验收/failure_paths 等）+ 对话策略（澄清 → 起草 → **提示人闸**） |
| **禁令条文入 pack** | comms system 必含：永不签发 human_gate（SPEC 06 §3 禁令 B）· 写盘仅 `docs/tasks/`+invoke 草稿（C3 边界预告）· Skills≠verify（§8） |
| **意图路由** | 默认 **product**；显式「立项 / 开 task / 写 SPEC」类意图 → comms；**不确定回退 product**（宁可漏进 comms）；判定器形态=规则/关键词纯函数（本波 **不引入** LLM 判定） |
| **分 session** | pack=comms 与 product **分 thread**；不共用 system；本波交付判定器 + pack 渲染，session 管理接线**不在本波**（SPEC §9 条文落地到 pack 元信息：`session_scope="comms"` 标记） |
| **Capability 声明** | pack 元信息可声明可用 `harness.verify`/`harness.task_lint`（C1 已交付）；**不在本波调用**（Policy 默认关保持） |
| **product 侧零影响** | 现有 prompts render/templates 行为不变（旧测绿）；comms 为新增 pack |
| **模块** | 不新增一级模块 |

---

## 范围

1. `render_pack("comms", ...)` 纯函数：槽位链装配（FRAGMENT 注入 + task 字段清单 + 对话策略 + 禁令条文）  
2. `route_intent(text)` 纯函数判定器（规则/关键词；默认 product；显式立项意图 → comms；回退 product）  
3. pack 元信息（`session_scope="comms"` · capability 声明 · 版本）  
4. api 单测（全纯函数 · 不连真 LLM）  
5. 文档/图谱备注；ruff + graph-compile

## 非范围

- **C3** 受控写盘 · **C4** `/obs` UI · C1 返工  
- 新增 HTTP 路由 / 接线到 chat 端点 / session 管理实现  
- LLM 驱动的意图判定（本波规则/关键词即可；升级另议）  
- 改 product pack 或业务 Chat / lg-rag 任何行为  
- 真调 `harness.*` Capability · 改 Policy 默认  
- 拷贝 FRAGMENT 后双写漂移（须引用仓内真值或构建期生成并校验）

---

## 验收标准

- [ ] `render_pack("comms")` 输出含：FRAGMENT_00_delegate_only 与 FRAGMENT_hat_reanchor 内容（子串断言）· task 字段清单 · 「永不签发 human_gate」禁令条文（断言）  
- [ ] FRAGMENT 内容与仓内 `docs/harness/prompts/` 真值一致（测试读真值文件对比 · 防拷贝漂移）  
- [ ] `route_intent`：参数化用例——「帮我开个 task/立项/写个 SPEC」→ comms；普通业务问句 → product；空/模糊 → product（回退）  
- [ ] pack 元信息含 `name="comms"` · `session_scope="comms"` · `version`；product 侧渲染零变化（既有 `render()`/`get_template()` 签名与行为不变 · 旧测绿）  
- [ ] `route_intent` 返回值严格二值字面量 `"comms" | "product"`（无第三值；异常/None 输入 → product）  
- [ ] 无新增 HTTP 路由（`router.py` 零 diff）；不 import `app.ops.session`/chat 流路径  
- [ ] `01_modules.md` 备注；若增 `implementedBy` → G-L2 indexes 同步  
- [ ] `ruff check` 触及路径绿；pytest 相关绿；`./scripts/graph-compile.sh` exit 0  
- [ ] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 意图误判（应为 product 判 comms） | 回退 product（默认态）；comms 入口须显式 | 是 | 无（C2 无 UI） |
| FRAGMENT 真值文件缺失 | 渲染报错（启动/测试期暴露 · 不静默降级为空槽位） | 修文件 | 测试红 |
| pack 槽位缺字段 | 渲染报错（明确缺哪个槽位） | — | 测试红 |
| 模型输出「已代签」字样 | pack 禁令条文压制 + C3 人确认兜底（SPEC §6） | — | 后续波验收 |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md` §4 · §6 · §8 · §9  
3. 只读参考：`app/ops/prompts/render.py` · `templates.py` · `docs/harness/prompts/FRAGMENT_00_delegate_only_v1_zh.md` · `FRAGMENT_hat_reanchor_v1_zh.md`  
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  

---

### 自检结论

> **10-task** · 2026-09-01 · 分支 `task/host-comms-prompt-pack` · docs-only 本帽（不改 `app/` / `tests/`）· HG-AUDIT-R1 保持 **pending**（本帽不签发）

**现网事实核对**（只读 `app/ops/prompts/` · `docs/harness/prompts/` · `docs/_tech_graph/l1/01_modules.md` · 结论：现网与 task 陈述**全部一致**，无字段/文件不符需修正；1 处开放钉（模块归属）已按现网钉死）

| 核对项 | 现网事实 | 结果 |
|---|---|---|
| `render.py` API 形态 | `render(template_id, variables=None, *, slots=None) -> str`（slots 以 `<!-- slot:name -->` 块追加正文后）；`get_template`；`PromptTemplateNotFoundError(KeyError)`；缺变量抛 `KeyError` | ✅ 00 定夺 `render_pack("comms", slots)` 为新增纯函数，与既有 render/slots 机制兼容 |
| `templates.py` registry | `TEMPLATES` dict（version/body）；仅两枚：`lg_rag.intent.system` v1 · `lg_rag.supervisor.system` v1（含 `{catalog_block}` 变量） | ✅ 「product 侧零影响」可检验：旧模板集合与渲染行为不变 |
| FRAGMENT 真值文件存在性 | `docs/harness/prompts/FRAGMENT_00_delegate_only_v1_zh.md` ✓ · `FRAGMENT_hat_reanchor_v1_zh.md` ✓ 均存在 | ✅ task 前置「kit ≥1.10 FRAGMENT 已 sync 仓内」属实 |
| prompts 图谱归属行 | `01_modules.md` 模块表无 `app/ops/prompts/**` path glob；模板 id 全部 `lg_rag.*` 且被 lg_rag supervisor/intent 消费 → **归属 `lg_rag` 行（L27）** | ✅ 已将 graph_delta 的开放钉「由 10 核现网钉」钉死为 lg_rag 行备注（记录性修正，非 00 定夺实质变更） |
| SPEC 06 §15 | `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md` 存在；§15「思考轮控制（10-spec 回填）」在 | ✅ 本 task 思考轮由 SPEC 承载（W4 合法） |

**00 定夺范围实质**：**零改动**（slug / 纯函数层无新路由 / 槽位链=FRAGMENT 真值+task 字段清单+对话策略+禁令条文 / 意图路由默认·回退 product / 分 session 元信息 / product 侧零影响 / 不新增一级模块 —— 全部保留）；仅补 2 条验收钩（pack 元信息字段钉死 + product 渲染签名不变 · `route_intent` 严格二值回退）并将模块归属开放钉钉死。

**lint 与禁区**

- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_prompt_pack.md` → **PASS**（exit 0 · **W4 合法**：无思考轮节 · 思考轮由 SPEC 06 §15 承载，本 task 为 SPEC 落地执行波）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**
- [x] `app/` · `tests/` 零改动；人工闸状态未改（HG-AUDIT-R1 仍 pending · HG-GRAPH-MODULES approved 未动）
- [x] invoke 落盘：`docs/harness/invokes/by-task/host-comms-prompt-pack/invoke_20260901_10_task_host-comms-prompt-pack.md`（hat_id=10-task）
- 下一棒：**20-task-audit** R1 落盘 → 00 代签 HG-AUDIT-R1 → 30 开工

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C1 CLOSE（#114/#115）后起草 C2；钉 slug=`host-comms-prompt-pack`；纯函数层（无新路由）；槽位链=kit FRAGMENT 真值+task 字段清单+对话策略+禁令条文；意图路由规则判定器（默认/回退 product）；分 session 元信息标记 |
| 2026-09-01 | **10-task**：现网核对全一致（render/templates API 形态 ✓ · FRAGMENT 两文件存在 ✓）；模块归属开放钉钉死为 `01_modules.md` `lg_rag` 行（L27）备注；补验收钩 2 条（pack 元信息字段+product 渲染签名不变 · `route_intent` 严格二值回退 product）；补 `### 自检结论`（W4 合法：思考轮由 SPEC 06 §15 承载）；invoke 落盘；00 定夺实质零改 · HG-AUDIT-R1 保持 pending · 下一棒 20-task-audit |
