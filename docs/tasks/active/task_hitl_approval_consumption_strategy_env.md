# Task：hitl-approval-consumption-strategy-env（T3 · D3 strategy 候选 map env 追加口 · 最小独立）

> **状态**：`draft`  
> **类型**：**SPEC 承接**（SPEC v1 · HG-SPEC-SIGNOFF=approved 2026-10-10）  
> **依据**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（**SPEC 文档当前在 `spec/hitl-approval-consumption` 分支 · 随首个实现 PR 一并带入 master**）——本 task 承接 D3（strategy 候选 map env 口 · 最小独立）· Q4 · FP-5 · A4（+ A5/A8 存续面）  
> **分支**：`task/hitl-approval-consumption-strategy-env`（base：`master` 4d905e0 · 禁止 master 直改）  
> **拆分**：T3（本）与 T1/T2 **无依赖 · 可插队先行**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl-approval-consumption-strategy-env` |
| **git_branch** | `task/hitl-approval-consumption-strategy-env` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测为主：env 不设时 `get_candidate_capability_ids` 各 key（含未知 key）解析结果对 master 逐字节零 diff 断言 + 设 env 后追加/去空去重/strip 语义断言 + 未知 key 追加断言 + FP-5 断言（env 含高危/写 id 仍被下游 ∩visible/deny_high_risk/Policy 裁）+ env 读取时机断言（调用点读取 · 禁 import 时固化）；全量 pytest 回归零新增红 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（行备注 · 不新增一级模块） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` lg_rag 行（strategy 归属段）在册备注 |
| **graph_delta_note** | strategy 非一级模块（归属 lg_rag 行备注段 · 承既有「路径覆盖补记」裁定）：lg_rag 行补 env 追加口说明 → G-L1 行备注同步，HG-GRAPH-MODULES 随 30 回写由 00 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | SPEC 承接 task · 机制接线增量无 wiki 条目变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30 → 40 → PR+CI 绿 → 图谱回写 → CLOSE |
| **freeze_id** | 无（零新表/零新列 · payload jsonb 增键 · 零新 SSE 事件类型 · 零 alembic） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 维护者签 · 00 代录 2026-10-10（授权「授权00签收所有过程文档」）· 初稿 lint PASS |
| HG-AUDIT-R1 | **approved** | 30 | 维护者签 · 00 代录 2026-10-10 · 依据 R1 审查 PASS（docs/harness/reviews/task_hitl_approval_consumption_strategy_env_audit_R1_20261010.md · nit×3 非阻塞留 30/40） |
| HG-GRAPH-MODULES | **approved** | 30 | 维护者签「在册」（strategy 归属 lg_rag 行备注段）· 00 代录 2026-10-10 · 30 交付时 lg_rag 行备注回写义务在案（F4/TC3） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

SPEC v1 §1 缺口 3（第四道门）：`app/ops/strategy/config.py:14-23` `CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]` 为**静态候选 map**（无 env 口），builder 节点 `allowed = candidates ∩ visible`（`app/ops/strategy/builder.py:177-182`）使 testing.write.echo 类新 capability 生产路径 plans 永不可达（40 invoke :33 · live 首发 SSE 帧实证静态五枚 · 测试等价 shim `CANDIDATE_CAPABILITY_IDS` 运行期覆盖补位如实登记）。

**一句话目标**：给 strategy 候选 map 开 **env 追加口** `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`（逗号分隔 · strip · 去空去重 · **默认不设=解析结果对 master 逐字节零 diff**）——env 只抬候选层，下游 ∩visible/deny 判序/Policy 写闸全链不动（Q4 · S1 裁定）。最小独立 task：与 T1/T2 无依赖，可插队先行合并。

---

## 现状锚点（只读 · 30 必读 · 10 已逐行实读 · base `4d905e0`）

| 锚点 | 实证 |
|------|------|
| `app/ops/strategy/config.py:1-6` | 模块 docstring：按 key 查显式 map · **禁止 None=全开** · 未知 key → 空列表（fail-closed）· 测试可 patch `CANDIDATE_CAPABILITY_IDS` 覆盖 |
| `app/ops/strategy/config.py:14-23` | `CAPABILITY_ALLOWLIST_BY_KEY`：supervisor 五枚静态 + default=最小只读集（:11）——无 env 口 |
| `app/ops/strategy/config.py:25-26` | `CANDIDATE_CAPABILITY_IDS: list[str] | None = None`——测试/运维显式覆盖口（非 None 优先于 map · 注释「禁止用 None 表示全开」）· **定位是测试钩子 · 不复用作 env 口**（Q4 S3 弃选在案） |
| `app/ops/strategy/config.py:29-45` | `get_candidate_capability_ids`：覆盖口非 None → 直返（:39-40）；map 未命中 → `[]`（:43-44）；命中 → `list(mapped)`（:45）· **env 追加点=map 解析结果之后** |
| `app/ops/strategy/builder.py:177-182` | 调用面：节点函数内每轮调 `get_candidate_capability_ids(agent_type, mode)` → `build_allowlist_from_candidates(candidates, visible_ids=visible_ids)`（∩visible + stripped span 台账）——**下游裁剪全链不动** |
| `docs/_tech_graph/l1/01_modules.md` lg_rag 行 | strategy 归属裁定：「`app/ops/strategy/**`（S1 薄包 · 消费方 `lg_rag/multi` · 非一级模块 · 承 prompts 先例归属本行）」——图谱回写落 lg_rag 行备注段 |
| env 解析先例 | `app/ops/capability/delegation.py:100-107`（env 读取 strip/lower/回退形态）· `baseline.py` `OPS_CAPABILITY_ALLOW_WRITE_TAGS` 逗号分隔先例（testing-write-capability task） |
| 证据源 | `docs/harness/invokes/by-task/testing-write-capability/invoke_20261009_40_verify_testing-write-capability.md` :33（live 静态五枚实证 + shim 补位登记） |

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **env 形态** | `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`：逗号分隔 · 逐项 strip · **去空去重**（保序去重）· **默认不设=解析结果对 master 逐字节零 diff**（不设/全空白 → 追加集为空 · 返回路径与现状一致） |
| **追加语义（Q4 · S1）** | `get_candidate_capability_ids` 在 **map 解析结果之后追加 env 集**；**含未知 key**（map 未命中=[] 也追加 · env 是运维显式声明 · fail-closed 管默认不管显式）；返回仍为新 list（不改 map 本体） |
| **覆盖口优先级不动** | `CANDIDATE_CAPABILITY_IDS` 非 None 直返分支（:39-40）**一行不动**——测试钩子纯净（覆盖口生效时不追加 env · 避免测试面被环境意外污染 · 留 20 复核）；**禁复用该覆盖口当 env 口**（Q4 S3 弃选：半径过大 · 定位是测试钩子） |
| **env 读取时机** | env 在 `get_candidate_capability_ids` **调用点读取**（函数内读 `os.environ`）· **禁模块 import 时固化**（builder.py:177 每轮调用 · 与 `baseline_filter` 调用点读取先例同形态；测试内 monkeypatch 直接生效 · 不依赖 import 顺序巧合） |
| **下游闸全链不动** | candidates 仍经 ∩visible（builder.py:177-182 · stripped 台账照旧）；deny 判序（`registry.py::_match_filter` :112-140 · deny_high_risk 在 deny_write 前）与 Policy 写闸（`policy.py:96-105`）diff 空；`_subtasks_have_valid_tool_ids` 照旧——**env 只抬候选层，不是放行口** |
| **map 静态成员零改** | `CAPABILITY_ALLOWLIST_BY_KEY` 既有成员（supervisor 五枚 + default）与 `MINIMAL_READONLY_CAPABILITY_IDS` 一行不动 |
| **台账** | env 追加集生效时记候选 id 列表 + 基数（logger/span · 配置非敏感）；未设 env 不记（零 diff） |

---

## 范围

- [ ] **F1 · env 追加口**：`strategy/config.py` 增 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS` 解析（逗号分隔/strip/去空去重/调用点读取）+ `get_candidate_capability_ids` map 解析后追加（含未知 key · 覆盖口分支不动）
- [ ] **F2 · 台账**：env 追加集生效记录（候选 id 列表 + 基数）
- [ ] **F3 · 测试**：验收 TC1–TC3 逐条断言化（含 FP-5 下游裁剪断言与 B1 旧测全绿亲跑）
- [ ] **F4 · 图谱同步**：`docs/_tech_graph/l1/01_modules.md` lg_rag 行（strategy 归属段）在册备注回写（G-L1 · HG-GRAPH-MODULES 随 30 回写由 00 代录）

### 非范围

- ❌ T1（消费门/unlock 回填）与 T2（自动 resume）全部面——本 task 无依赖 · 不等待不合流
- ❌ `CAPABILITY_ALLOWLIST_BY_KEY` / `MINIMAL_READONLY_CAPABILITY_IDS` 静态成员任何改动
- ❌ `CANDIDATE_CAPABILITY_IDS` 覆盖口语义（优先级/测试钩子定位）任何改动
- ❌ builder/scenario 裁剪逻辑（∩visible/stripped/scenario_trim）任何改动；deny 判序/Policy 写闸/gateway 闸链
- ❌ 新 capability 注册（testing.write.echo 加载/可见性属 testing-write-capability 既有 task 面）；前端/UI
- ❌ SPEC 文档本身任何改动（在 spec 分支 · 随首个实现 PR 带入 master）

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| — | HG-AUDIT-R1 / HG-GRAPH-MODULES pending 即 30 | **拒开工**（GATE_VERIFY 拦 · 真值在本表人工闸） | 是 | 是 |
| FP-5 | env 口注入高危/写 capability id | 下游 ∩visible + deny_high_risk（判序在前）+ deny_write + Policy 写闸全链仍在——**断言「env 含高危/写 id 仍被裁」**（候选层抬升 ≠ 可见/可签发/可执行） | 是 | 否 |
| 实操-A | env 解析坑：连续逗号/首尾空白/重复项/全空白 | strip + 去空 + 保序去重；全空白=不设（零 diff）；断言化四例 | 是 | 否 |
| 实操-B | env 在 import 时固化为模块级常量 → 测试 monkeypatch 不生效/运行期改 env 无效 | 调用点读取钉死（函数内读 env）；测试断言「monkeypatch 后直接生效 · 无需 reload」 | 是 | 否 |
| 实操-C | 未知 key 场景漏追加（map 未命中直返 [] 把 env 集丢掉） | 追加逻辑在 map 解析结果**之后**统一执行（含 [] 分支）；未知 key + env 断言化（SPEC「含未知 key」裁定） | 是 | 否 |
| 实操-D | 覆盖口 `CANDIDATE_CAPABILITY_IDS` 非 None 时被 env 追加污染 → 既有测试钩子语义漂移 | 覆盖口分支一行不动（:39-40 直返不追加）；断言「覆盖口生效时 env 集不混入」 | 是 | 否 |
| 实操-E | 未设 env 时返回对象/顺序微差（如去重改了保序、追加了空 list 操作改返回 identity） | TC1 逐字节零 diff 断言（各 key 含未知 key · 与 master 基线对拍） | 是 | 否 |
| 实操-F | `npx spec-wave task lint` / `lint-wiki-delta` 红 | 30 返工修结构 | 是 | 否 |

---

## B1 · 旧测影响面（10 已实扫落盘 · 20-audit 核查清单 · 30 亲跑义务）

| 文件 | 断言面 | 预期 |
|------|--------|------|
| `tests/test_strategy_builder.py` | BUILDER_CAP_FILTER/allowlist 构建面 | 零 diff 原样绿（env 未设） |
| `tests/test_strategy_scenario.py` | scenario_trim 两阶段裁剪面 | 零 diff 原样绿 |
| `tests/test_lg_rag_supervisor_capability_catalog.py:50-57` | supervisor 可见集成员断言（mock_get_issue_status/utc_now_iso） | 零 diff 原样绿（env 未设候选不变） |
| `tests/test_prompt_assets.py` / `test_prompt_assembly.py` | 目录渲染进 prompt 断言 | 零 diff 原样绿（候选不变 → 渲染不变） |
| `tests/test_capability_domain_allowlist.py:102-112` | deny 判序钉死 | 原样绿（反回归存续） |
| `tests/test_capability_testing_write.py` | testing.write.echo shim 覆盖面（`CANDIDATE_CAPABILITY_IDS` 运行期覆盖） | 原样绿（覆盖口分支不动 · 实操-D 断言兜底） |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved 后方可勾选下列码项
- [ ] **TC1（env 口零 diff/追加语义 · SPEC A4）**：① 不设 env → `get_candidate_capability_ids` 各 key（supervisor/default/**未知 key**）解析结果对 master 逐字节一致（返回 list 内容与顺序对拍）② 设 env → candidates 含追加 id（map 命中 key 与未知 key 两例）且 ∩visible/stripped 语义不变 ③ 解析断言：strip/去空/保序去重/全空白=不设 ④ 覆盖口生效时 env 集不混入
- [ ] **TC2（FP-5 · 下游闸不动）**：env 含高危/写 capability id → 仍被下游裁（∩visible 不可见 · 或经可见性豁免路径仍被 deny_high_risk/deny_write/Policy 裁 · 按既有测试面选型断言并留痕）；`registry.py::_match_filter` 与 `policy.py` 闸序段 git diff 为空；`test_allow_tags_does_not_waive_deny_write` 原样绿
- [ ] **TC3（工程面 · SPEC A8 本 task 面）**：`pytest tests` 全绿；`ruff check app tests` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；图谱 lg_rag 行（strategy 归属段）备注回写 + HG-GRAPH-MODULES 00 代录行；env 生效台账断言（设则记 · 未设不记）
- [ ] B1 旧测清单全绿亲跑记录（命令 + 结果）落 40 invoke
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` PASS；`npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| **task 依赖** | **无**（与 T1/T2 无耦合 · 可插队先行合并；串行队列中独立验收） |
| SPEC（依据 · signed） | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（**当前在 `spec/hitl-approval-consumption` 分支 · 随首个实现 PR 一并带入 master**）——D3 + Q4 + FP-5 + A4 |
| 改动面锚点 | `app/ops/strategy/config.py:1-45` · `app/ops/strategy/builder.py:177-182` |
| 证据源 | `docs/harness/invokes/by-task/testing-write-capability/invoke_20261009_40_verify_testing-write-capability.md` :33（live 静态五枚实证 + shim 补位登记） |
| env 解析先例 | `app/ops/capability/delegation.py:100-107` · `app/ops/capability/baseline.py`（`OPS_CAPABILITY_ALLOW_WRITE_TAGS` 逗号分隔 · `docs/tasks/done/task_testing_write_capability.md`） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-16 capability 契约纪律：注册表 ≠ 注册中心 · 候选层 ≠ 放行口） |
| 上游任务范式 | `docs/tasks/done/task_host_v1_visibility_scenario_policy.md`（可见性/裁剪裁定先例）· `docs/tasks/done/task_testing_write_capability.md`（结构范式） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 + GATE_VERIFY）· 2. 本 task（钉死契约 + B1 + 验收标准）· 3. SPEC v1 §2 D3 + §4 Q4 + §5 FP-5 + §6 A4（分支路径同 T1）· 4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-16）· 5. `app/ops/strategy/config.py` 全文 + `app/ops/strategy/builder.py:150-200`（调用面）· 6. `tests/test_strategy_builder.py` + `test_strategy_scenario.py`（B1 面）· 7. `docs/tasks/done/task_testing_write_capability.md`（env 门控先例 · `OPS_CAPABILITY_ALLOW_WRITE_TAGS` 形态）· 8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题=SPEC v1 既定 D3 承接（缺口 3 第四道门 · 40 invoke :33 实证）；最小独立 task | no | — | none |
| R1 | 范围=env 解析+追加+台账+测试+图谱备注；静态 map/覆盖口/下游裁剪/T1/T2 面全非范围 | no | — | 无 |
| R2 | SPEC Q4=S1 env 追加集裁定存续（S2 全量覆盖难审计 · S3 复用测试钩子半径过大 · 双弃）；新增钉=覆盖口分支不动（env 不混入）+ 未知 key 追加 + 调用点读取 | no | — | 覆盖口生效时不追加 env 一钉留 20 复核（SPEC 未明示两键交互） |
| R3 | 交叉验证：builder.py:177 节点内每轮调用实证（调用点读取可行）· config.py:39-45 分支结构实证（追加点=map 解析后）· lg_rag 行 strategy 归属裁定在册 | no | — | 无 |
| R4 | failure_paths 推演 7 条（FP-5 + 实操 A–F · 解析坑/固化坑/未知 key 漏追加/覆盖口污染/零 diff 微差） | no | — | 无 |
| R5 | 验收口径机断化收敛（TC1–TC3 映射 SPEC A4/A5/A8 · 逐字节对拍/断言/diff 空/EXIT=0） | yes | 单文件小改动面 · 裁定全存续 · 锚点实读闭环 | 见 R2 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R2

### R0 · 问题框定

SPEC v1 D3 已签收（Q4=S1 env 追加集）。实读：SPEC v1 相关节 + `strategy/config.py` 全文 + `builder.py:150-200` 调用面 + 40 invoke :33 证据段。需求边界无歧义：只抬候选层，不动任何下游闸。

### R1 · 范围钉死

改动面四件（F1–F4）：env 解析+追加 · 台账 · 测试 · 图谱 lg_rag 行备注。划出：静态 map 成员、`CANDIDATE_CAPABILITY_IDS` 覆盖口语义、builder/scenario 裁剪逻辑、deny/Policy/gateway 闸链、新 capability 注册、T1/T2 全部面。独立理由：单文件小改动 + 验收 A4 自足（零 diff 对拍+追加断言+FP-5 断言）· 与消费门/自动 resume 零耦合 · 插队先行可缩短关键路径。

### R2 · 方案裁定

**SPEC 裁定存续（不重开）**：Q4=S1 env 追加集（S2 env JSON 覆盖整 map=易误伤默认只读集难审计 · S3 复用 `CANDIDATE_CAPABILITY_IDS`=半径过大且定位是测试钩子 · 双弃在案）。

**新增钉一 · 追加点=map 解析结果之后（含未知 key）**。实证 config.py:39-45 分支结构：覆盖口直返 → map 命中返 list → 未命中返 []。env 追加统一作用于 map 解析结果（命中 list 与未命中 [] 皆追加）——SPEC「含未知 key · fail-closed 管默认不管显式」原样落地；覆盖口分支（:39-40）一行不动即「测试钩子不被环境污染」。

**新增钉二 · 调用点读取**。builder.py:177 实证为节点函数内每轮调用 → env 函数内读取即每轮生效 · 无 import 时固化面；测试 monkeypatch 直读生效（对齐 testing-write-capability 钉死契约「禁止依赖 import 顺序巧合」精神）。

**新增钉三 · 解析形态**。逗号分隔/strip/去空/保序去重/全空白=不设——承 `OPS_CAPABILITY_ALLOW_WRITE_TAGS` 先例形态，零 diff 由「不设=追加集为空且返回路径不变」保证（TC1 逐字节对拍兜底）。

### R3 · 交叉验证

- **调用面实证**：`get_candidate_capability_ids` 唯一生产调用点=builder.py:177（节点函数内）——无模块级固化消费方（与 BUILDER_CAP_FILTER 常量不同性质）。
- **图谱归属实证**：01_modules.md lg_rag 行已载「`app/ops/strategy/**` 非一级模块 · 归属本行」裁定 → 回写落 lg_rag 行备注段，无新行无新边。
- **FP-5 链复核**：env 追加 id → candidates → ∩visible（baseline deny_write/deny_high_risk 判序 :112-140 在前）→ 计划校验 → 签发判定 → Policy 写闸——四层下游任一皆可裁 · env 只影响第一层输入。
- **零 diff 论证**：不设 env → 追加集空 → map 命中返 `list(mapped)`（同现状）· 未命中返 []（同现状）· 覆盖口直返（同现状）——三分支各自零 diff · TC1 对拍机断。

### R4 · failure_paths 推演

FP-5（env 注入高危/写 id）落 TC2 断言（下游四层裁剪任选既有测试面断言并留痕）。实操坑六条：解析四例（A · 断言化）、import 固化（B · 调用点读取钉+monkeypatch 断言）、未知 key 漏追加（C · 追加点钉+断言）、覆盖口污染（D · 分支不动+断言）、零 diff 微差（E · 逐字节对拍）、lint 红（F）。每条可机断。

### R5 · 验收口径机断化收敛

TC1（逐字节对拍+追加+解析四例+覆盖口隔离）/TC2（FP-5+diff 空+钉死测试原样绿）/TC3（工程面+台账断言）均可对命令输出或断言机断；B1 六文件清单全绿亲跑义务落 40 invoke。单文件小改动面无方案分叉 → early_stop。

---

### 自检结论（执行者）

（30/40 回填）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 10-task 落稿（骨架先行增量落盘 · SPEC v1 signed 承接 · R0–R5 · HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending → 30 拒开工） |
