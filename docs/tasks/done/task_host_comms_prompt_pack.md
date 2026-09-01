# Task：Host C2 · comms Prompt Pack（PromptAssembly pack=comms）

> **状态**：completed（2026-09-01 CLOSE · PR [#116](https://github.com/Cyning12/ops-desk-api/pull/116) MERGED）  
> **类型**：Prompt 工程 / Host 沟通轨实现  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](../../spec/agent-infra/06_host_comms_boundary_spec_v0.md)（**signed** · #111）§4（意图路由）· §5（产物路径）· §6（闸纪律）· §9（session 隔离）· §10（C2 行）  
> **前置**：C1 CLOSE · [`task_host_harness_cli_capability`](./task_host_harness_cli_capability.md) · [#114](https://github.com/Cyning12/ops-desk-api/pull/114)；H4 方向 ✓ · kit ≥1.10 FRAGMENT 已 sync 仓内（`docs/harness/prompts/FRAGMENT_00_delegate_only_v1_zh.md` · `FRAGMENT_hat_reanchor_v1_zh.md`）  
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
| **related_pr** | `#116` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C 轨串行：C0 ✓ → C1 ✓ → **C2** → C3；C4 跨仓 web 可后与 C3 尾并行 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | approved | 30 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** · 见 `docs/harness/reviews/task_host_comms_prompt_pack_audit_R1_20260901.md`（R1 pass · 内容零阻塞） |
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

- [x] `render_pack("comms")` 输出含：FRAGMENT_00_delegate_only 与 FRAGMENT_hat_reanchor 内容（子串断言）· task 字段清单 · 「永不签发 human_gate」禁令条文（断言）  
- [x] FRAGMENT 内容与仓内 `docs/harness/prompts/` 真值一致（测试读真值文件对比 · 防拷贝漂移）  
- [x] `route_intent`：参数化用例——「帮我开个 task/立项/写个 SPEC」→ comms；普通业务问句 → product；空/模糊 → product（回退）  
- [x] pack 元信息含 `name="comms"` · `session_scope="comms"` · `version`；product 侧渲染零变化（既有 `render()`/`get_template()` 签名与行为不变 · 旧测绿）  
- [x] `route_intent` 返回值严格二值字面量 `"comms" | "product"`（无第三值；异常/None 输入 → product）  
- [x] 无新增 HTTP 路由（`router.py` 零 diff）；不 import `app.ops.session`/chat 流路径  
- [x] `01_modules.md` 备注；若增 `implementedBy` → G-L2 indexes 同步（未增 implementedBy → 无需同步）  
- [x] `ruff check` 触及路径绿；pytest 相关绿；`./scripts/graph-compile.sh` exit 0  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

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

### 自检结论（执行者）

> **30+40** · 2026-09-01 · 分支 `task/host-comms-prompt-pack` · GATE_VERIFY PASS（三闸 approved · verify 开工前/收尾各一次均 exit 0）

**实现摘要**

- 新增 `app/ops/prompts/packs.py`：`render_pack("comms", *, slots=None, base_dir=None) -> PromptPack`（独立装配函数 · 不改 `render()`；slots 沿用 `<!-- slot:name -->` 机制 · 传入时须含 `REQUIRED_SLOTS=("task_slug","hat_id")` 缺则 `PromptPackError` 点名缺哪个槽位）· `route_intent(text) -> Literal["comms","product"]` · 元信息 `name="comms"`/`session_scope="comms"`/`version="v1"`/`capabilities=("harness.verify","harness.task_lint")`（仅声明不调用）
- **FRAGMENT 注入形态（30 定）**：**运行时读仓内真值文件**（`docs/harness/prompts/FRAGMENT_*.md` · 仓根由 `packs.py` 相对解析 `parents[3]` · `base_dir` 参数可覆盖供测试）。理由：真值文件即单一 SoT，运行时读=注入内容逐字即真值，**物理上不可能拷贝漂移**；仓内无构建期步骤可承载「内嵌生成」，若内嵌反而引入第二份拷贝。部署形态风险（`docs/` 不在 `app/` 包内）由 failure_paths 行 2 兜底：文件缺失/为空 → `PromptPackError` 明确报错不静默降级（测试以 `tmp_path` 断言）；且本波为纯函数层无部署接线（无新路由），路径基准问题留 C3/C4 接线时复核
- **关键词词表（30 定）**：SPEC §4 例示作种子——`立项 / 开task / 开 task / 开个task / 开个 task / 起草task / 起草 task / 写spec / 写 spec / 写个spec / 写个 spec / 起草spec / 起草 spec / 拆波次 / 走harness / 走 harness / harness流程 / harness 流程`（匹配前 `strip().lower()`）；词表外业务措辞一律回退 product（如「这个 spec 字段含义」→ product 有断言）
- product 侧零影响：`render.py`/`templates.py` 零 diff · `__init__.py` 仅追加导出 · `router.py` 零 diff（git status 核实）· `packs.py` 不 import `app.ops.session`/`app.ops.chat`（AST 断言锁定）
- R1 非阻塞 4 条处置：① FRAGMENT 形态=运行时读（上文）② 词表已钉并记录（上文）③ **跨 session 交还本波未做**（留 C3/C4 · 无顺手实现）④ `render_pack` 为独立装配函数，仅复用 slot 注释机制，验收条 4 钩住 product 零影响（`test_product_render_unchanged` + 旧测 8 用例绿）

**自检命令（逐条退出码 · pytest 用 CI 等价口径）**

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npx --yes dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_host_comms_prompt_pack.md` | 0 | VERIFY: PASS（开工前 + 收尾各一次） |
| `ruff check app/ops/prompts/ tests/test_prompt_packs.py`（触及路径） | 0 | All checks passed |
| `ruff check app tests`（全量参考） | 1 | 2 处**既有**问题（`app/ops/rag/tokenizer.py` UP035 · `tests/test_rag_chunker.py` I001 · git stash 核实 HEAD 既有 · 非本波触及 · 按 P-07 不顺手改） |
| `DATABASE_URL=postgresql+asyncpg://127.0.0.1:1/invalid .venv/bin/python -m pytest tests -q` | 0 | **543 passed · 39 skipped**（新测 44 用例 + 旧测 `test_prompt_assembly.py` 8 用例零破坏） |
| `./scripts/graph-compile.sh` | 0 | 9 graphs OK（生成物 `shared/graph.json` 仅 `generated_at` 刷新） |
| `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` | 0 | PASS |
| `npx --yes dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_prompt_pack.md` | 0 | PASS（W4 合法豁免 · 思考轮由 SPEC 06 §15 承载） |

**测试清单**：`tests/test_prompt_packs.py`（新增 44 用例：槽位填充/FRAGMENT 子串/真值逐字一致/禁令条文/task 字段清单/对话策略/缺文件·空文件·缺槽位报错/未知 pack/slots 追加/元信息/route_intent 参数化 comms 9 + product 7 + 回退 7 + 严格二值/纯函数可重入/product 渲染不变/AST import 边界）；`tests/test_prompt_assembly.py`（旧 8 用例 · 零破坏）

**已知未测项**：真 LLM 消费 pack system（task 非范围 · 本波纯函数层）；`base_dir` 缺省解析在部署/打包环境的路径有效性（无部署接线 · failure_paths 行 2 报错语义已测）；意图误判的运行时跨 session 交还（R1 非阻塞 ③ · 留 C3/C4）；`harness.*` capability 真调用（仅声明 · Policy 默认关保持）

**禁区核对**：未切分支/未 push/未开 PR · 未签任何 human_gate · 未做跨 session 交还 · 未改 product 行为 · 无新 HTTP 路由

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C1 CLOSE（#114/#115）后起草 C2；钉 slug=`host-comms-prompt-pack`；纯函数层（无新路由）；槽位链=kit FRAGMENT 真值+task 字段清单+对话策略+禁令条文；意图路由规则判定器（默认/回退 product）；分 session 元信息标记 |
| 2026-09-01 | **10-task**：现网核对全一致（render/templates API 形态 ✓ · FRAGMENT 两文件存在 ✓）；模块归属开放钉钉死为 `01_modules.md` `lg_rag` 行（L27）备注；补验收钩 2 条（pack 元信息字段+product 渲染签名不变 · `route_intent` 严格二值回退 product）；补 `### 自检结论`（W4 合法：思考轮由 SPEC 06 §15 承载）；invoke 落盘；00 定夺实质零改 · HG-AUDIT-R1 保持 pending · 下一棒 20-task-audit |
| 2026-09-01 | **20** R1 **pass**（内容零阻塞；非阻塞 4 条已录审查文）· **00** 代签 `HG-AUDIT-R1` → approved；可派 30 |
| 2026-09-01 | **30+40**：实现 `app/ops/prompts/packs.py`（`render_pack("comms")` 运行时读 FRAGMENT 真值 + `route_intent` 规则判定器 + pack 元信息）· 新测 `tests/test_prompt_packs.py` 44 用例 · 图谱 lg_rag 行备注+人签记录 · 验收 9 条全勾 · 自检全绿（pytest 543 passed · graph-compile/lint-wiki-delta/verify exit 0）· R1 非阻塞 4 条逐项处置（跨 session 交还**未做**留 C3/C4）· invoke 落盘 · **不 CLOSE（留给 00）** |
| 2026-09-01 | **00 CLOSE**：PR [#116](https://github.com/Cyning12/ops-desk-api/pull/116) MERGED（CI 三绿）；无 Alembic；00 独立复跑 543 passed / ruff 净 / router 零 diff；归档 done/ · Hub 补登 · CLOSE invoke 留档 |

---

30+40 已交付；00 关账复检：独立复跑 pytest CI 等价 **543 passed / 39 skipped** · ruff 触及路径净 · router.py 零 diff · PR #116 CI 三绿后 squash MERGED。

---

## 关账（CLOSE）

| 项 | 值 |
|---|---|
| PR | [#116](https://github.com/Cyning12/ops-desk-api/pull/116) **MERGED** 2026-09-01 |
| 交付 | `app/ops/prompts/packs.py`（`render_pack("comms")` 运行时读 FRAGMENT 真值 + `route_intent` 规则判定器）+ 44 纯函数用例 |
| 生产 | 无 Alembic；无新路由；product 侧零影响（纯函数层 · 未接线） |
| 归档 | 2026-09-01 · 00 关账 · 维护者 Prompt 授权 |

### KPI

Task_KPI%: 100 · D1 范围钉死纯函数层无路由 · D2 闸齐（三代签 + 20 R1 pass）· D3 过程档齐（invoke 10/00/30_40 + R1 审查）· D4 图谱 lg_rag 行备注已随 #116 · D5 关账补登 2026-09-01
