# Task：graph-json-freeze-date-pin（仓卫生 · graph.json freeze_id/generated_at 日期漂移收口 · chore）

> **状态**：`draft`（10 落稿 · 闸 pending 待维护者签 · 禁 30 · 未 commit）
> **类型**：仓卫生 / 工具链产出确定性收口（chore · 零 `app/` 改动 · `graph_change_layer=none`）
> **依据**：`docs/tasks/close/close_ci_specwave_pin_align_20261017.md` §四·偏差 nit 第 2 条 + §七·后续建议第 1 条（「graph.json freeze_id 脱日期化另立案照登」——本 task 即该另立案）
> **分支建议**：`task/graph-json-freeze-date-pin`（base master 最新）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `graph_json_freeze_date_pin` |
| **git_branch** | `task/graph-json-freeze-date-pin` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 纯工具链产出面：同输入双跑字节级稳定断言（graph.json diff 为空）+ freeze_id 骨架语义 grep 断言 + arch-browser 消费方兼容实证 + PR CI（tech-graph）绿；零 `app/` diff 故 pytest 构造性恒等（触及面全绿即可） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（30 实判：仅改 scripts/graph_yaml_to_json.py 生成逻辑；图谱源 yaml/md 内容零改） |
| **graph_delta** | 无 |
| **graph_delta_note** | 本 task 不改图谱源；graph.json 为编译产出物，改造后其 freeze_id/generated_at 取值变化属预期交付（一次性落定，此后零漂移） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 确定性钉法事实回写 CLOSE 文档即可，无 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20-task-audit R1 → 维护者签闸 → 30（改造 + 本地实证）→ 40（PR CI 绿核验）→ PR → CLOSE |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-17 维护者签（00 代录 · 维护者会话授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-10-17 维护者签（00 代录）；20 R1 审查文 docs/harness/reviews/task_graph_json_freeze_date_pin_audit_R1_20261017.md（内容签收 · N-1~N-4 照登留 30 遵循） |
| HG-GRAPH-MODULES | approved | 30 | 全局真值 approved（docs/_tech_graph/l1/01_modules.md:63 · 20 R1 已核实）；2026-10-17 维护者签（00 代录） |

---

## 背景与目标

### 实证面（10 亲读 · 2026-10-17）

| 位置 | 现状 | 证据 |
|------|------|------|
| `scripts/graph_yaml_to_json.py:65-69` | `freeze_id` 以 `datetime.now(UTC).strftime('%Y%m%d')` 拼日期段（`OPS_DESK_API_TECH_GRAPH_FREEZE_<YYYYMMDD>_V1`），`generated_at` 同取 `datetime.now(UTC)` | 10 亲读 |
| `scripts/graph-compile.sh:58-59` | 每次 graph-compile 调 `graph_yaml_to_json.py` 重生成 `docs/_tech_graph/shared/graph.json` | 10 亲读 |
| `.github/workflows/tech-graph.yml:33` | PR / master push 均跑 `./scripts/graph-compile.sh`（日期漂移在 CI 同样发生） | 10 亲读 |
| 消费方 `docs/arch-browser/scripts/build_site.py:558-559` | `freeze_id` / `graph_generated_at` 仅**透传**进 `site-data.json`，无格式解析 | 10 亲读 |
| 消费方 `docs/arch-browser/web/app.js:55` | 仅字符串展示（`DATA.freeze_id` + `generated_at`），无解析 | 10 亲读（dist/app.js:55 同构拷贝） |
| 先例 `docs/_tech_graph/shared/99_mermaid_protocol.md:137` | 图谱 md 的 `generated_at` 已改 yaml 源内容戳 `sha256-<16hex>`（spec-wave ≥1.9.2 幂等）——graph.json 日期漂移为仅存非确定性面 | 10 亲读（l0/l1 各 md :4 均为 `sha256-<16hex>` 实证） |

### 风险照录（来自 CLOSE 文档，禁擅改史实）

`close_ci_specwave_pin_align_20261017.md` §四·2 原文照录：compile 后 `docs/_tech_graph/shared/graph.json` 仅 `freeze_id`（20261014→20261017）与 `generated_at` 两字段变化——系本仓 `graph_yaml_to_json.py:65-69` 以 `datetime.now(UTC)` 生成的日期字段，与 spec-wave 版本无关（3.0.1 下同构）；已 `git checkout --` 恢复，零混入该 PR（ci-pin 棒 6be8f3c2 实证）。§七·1 建议「freeze_id 脱日期化另立 task 收口」——本 task 即该另立案。

### 目标

`freeze_id` / `generated_at` 改为**确定性来源**，使同一图谱输入产出**字节级稳定**（跨日、跨机、CI/本地一致）。候选方向（30 定案，须先回 10 确认再动手若偏离下列三者）：

1. **内容 hash 派生**：由 graphs/nodes/edges 规范化内容 sha256 派生（对齐 md `generated_at: sha256-<16hex>` 既有先例）；
2. **环境变量注入**：`GRAPH_FREEZE_DATE` / `SOURCE_DATE_EPOCH` 类注入，默认值仍须确定性（禁裸 `now()` 回退）；
3. **git commit 时间**：取图谱源最近 commit 时间派生。

含 CI 防回归断言（freeze_id 生成路径不再含 `datetime.now`）。

---

## 范围

- [ ] **S1 · 方案定案与改造**（30）：`scripts/graph_yaml_to_json.py:65-69` 的 `freeze_id` / `generated_at` 生成改为确定性来源（三候选之一，30 定案并在 30 invoke 载明取舍理由）；保持 `freeze_id` 字符串骨架兼容（前缀 `OPS_DESK_API_TECH_GRAPH_FREEZE_` 与 `_V1` 后缀语义不破，见 FP-1）。
- [ ] **S2 · 本地字节级稳定实证**（30）：同输入连续双跑 `./scripts/graph-compile.sh`，`graph.json` diff 为空；跨 `TZ` 环境变量扰动复跑仍稳定。
- [ ] **S3 · 消费方兼容核验**（30）：`python3 docs/arch-browser/scripts/build_site.py` EXIT=0；`dist/site-data.json` 的 `freeze_id` 为非空字符串透传；grep 实证消费方（build_site.py / app.js）无格式解析依赖。
- [ ] **S4 · CI 实证**：PR 上 `tech-graph` workflow 绿；run 日志或 PR diff 实证 `graph.json` 无日期漂移残留。
- [ ] **S5 · 零 diff 纪律**：`git diff --stat` 仅触 `scripts/graph_yaml_to_json.py`、`docs/_tech_graph/shared/graph.json`（一次性落定产出）、本 task 与 invoke 档；图谱源 yaml/md、钉版文件零卷入。

## 非范围

- ❌ spec-wave **钉版 / 版本变更**（3.3.0 钉版已由 task_ci_specwave_pin_align 对齐，本案勿动 `GRAPH_CLI` 与任何 `.github/workflows/` 钉版字面）
- ❌ 图谱源改动（`docs/_tech_graph/**/*.graph.yaml` 与编译产出 md 内容；md `generated_at` 已是 sha256 内容戳，不动）
- ❌ arch-browser web 壳 / `app.js` / `build_site.py` 逻辑改动（消费方仅透传展示，本 task 只核验兼容）
- ❌ 业务 freeze 体系（`lg-rag-sse-v1` / `lc-evidence-http-v1` 等 SPEC freeze_id）——与 graph.json 元数据字段同名但不相干
- ❌ `graph.json` schema 结构变更（`schema_version` / graphs / nodes / edges 形状不动）
- ❌ 本起草阶段零任何文件改动（仅落盘本 task 与 10 invoke）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 方案破坏既有 freeze 校验语义（`spec-wave graph yaml check --graph-json` 或下游对 `freeze_id` 骨架 `OPS_DESK_API_TECH_GRAPH_FREEZE_*_V1` 有隐性断言 / `schema_version=graph_v2` 校验失败） | **不 merge**；30 先跑 check 矩阵实证校验面无 freeze_id 格式断言再定案；若确有断言，保留骨架仅替换日期段来源；无法两全则 STOP 回 10 重定案 | 是（revert 改造即复原） | PR 红 / check 失败 |
| FP-2 向后兼容破坏：旧 `freeze_id` 消费方异常（arch-browser build_site.py:558 透传断裂、web/app.js:55 展示乱码、dist/site-data.json 既有快照对比告警） | 新 `freeze_id` 必须保持字符串透传兼容（非空 str · 无新分隔符语义）；S3 grep + 构建实证未绿禁勾选 TC-3 | 是 | arch-browser 页面 freeze 信息显示异常 |
| FP-3 同输入双跑仍漂移（hash 混入不稳定源：字典序 / 绝对路径 / 环境差异） | 不勾选 TC-1；30 定位不稳定源（序列化 `sort_keys` / 相对路径化），修复后复跑；禁夹带 wall-clock 回退 | 是 | graph.json diff 不净 |
| FP-4 HG-AUDIT-R1 / HG-GRAPH-MODULES pending 即 30 | GATE_VERIFY **拒开工**（`npx spec-wave verify --task` BLOCKED） | 是 | — |
| FP-5 环境变量注入方案在 CI 未注入 / 默认值裸 `now()` 回退，致 CI 与本地产出不一致 | 默认值必须确定性（内容 hash 或 git 时间回退）；40 核验 CI run 产出与本地产出字节一致 | 是 | CI/本地 diff 分裂 |
| FP-6 顺手改钉版 / 图谱源 / 无关文件 | 拒收；diff 白名单仅 `scripts/graph_yaml_to_json.py` + `graph.json` 落定产出 + task/invoke 档 | 是 | PR 噪声 |

---

## 验收标准

- [ ] **TC-1（字节级稳定）**：同输入连续双跑 `./scripts/graph-compile.sh`（第二次跑前 `git checkout -- docs/_tech_graph/shared/graph.json` 或直接比对），两次产出 `graph.json` `cmp` / `git diff --exit-code` 为空；`TZ=America/New_York` 扰动复跑仍字节一致。30 invoke 贴双跑实证。
- [ ] **TC-2（freeze 语义保持）**：`grep -n "freeze_id" docs/_tech_graph/shared/graph.json` 输出匹配定案后的骨架断言（`OPS_DESK_API_TECH_GRAPH_FREEZE_` 前缀 + `_V1` 后缀，或 30 定案新骨架并在 invoke 载明）；`graph-compile.sh` 内 `graph yaml check` 全 OK（freeze 校验语义不破 · FP-1）。
- [ ] **TC-3（消费方兼容）**：`python3 docs/arch-browser/scripts/build_site.py` EXIT=0；`grep -n "freeze_id" docs/arch-browser/dist/site-data.json` 为非空字符串；`grep -rn "freeze_id" docs/arch-browser/scripts docs/arch-browser/web` 实证消费方仅透传 / 展示、无格式解析（FP-2）。
- [ ] **TC-4（CI 绿实证）**：PR 检查 `tech-graph` workflow 绿；40 invoke 贴 run 链接 + 日志摘录；CI 产出 `graph.json` 与本地同输入产出字节一致（FP-5 防 CI/本地分裂）。
- [ ] **TC-5（防回归断言）**：`grep -n "datetime.now" scripts/graph_yaml_to_json.py` 在 `freeze_id` / `generated_at` 生成路径无命中（若脚本他处合法使用须在 30 invoke 逐行说明）；30 在 CI 或脚本层留一条可复跑的防回归断言（grep 一行或 pytest 一例）。
- [ ] **TC-6（零越界）**：`git diff --stat master...HEAD` 仅含 `scripts/graph_yaml_to_json.py`、`docs/_tech_graph/shared/graph.json`、`docs/tasks/active/task_graph_json_freeze_date_pin.md`、invoke 档；零 `app/` diff → pytest/ruff 构造性恒等照登；钉版字面（`spec-wave@3.3.0`）零 diff。

## 依赖

- 出处钉案与授权来源：`docs/tasks/close/close_ci_specwave_pin_align_20261017.md`（§四·2 照录 + §七·1 另立案建议）
- 改造对象：`scripts/graph_yaml_to_json.py`（:65-69 日期漂移源）
- 调用链（只读确认）：`scripts/graph-compile.sh`（:58-59 调脚本）· `.github/workflows/tech-graph.yml`（:33）· `.github/workflows/lint-wiki-delta.yml`（钉版已 3.3.0，勿动）
- 消费方（只读核验）：`docs/arch-browser/scripts/build_site.py`（:558-559 透传）· `docs/arch-browser/web/app.js`（:55 展示）
- 内容戳先例：`docs/_tech_graph/shared/99_mermaid_protocol.md`（:137 · md `generated_at` sha256-<16hex> 幂等钉法）
- 历史漂移实证：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`（K8 · freeze_id 按日滚动首录）· `FEEDBACK_dsh_coding_kit_1_10_0_from_ops_desk_api_20260831.md`（R-graph-json · wall-clock + 日更 freeze_id 留档 P3）

## 给执行帽的必读列表

1. 本 task 全文（含 FP-1 freeze 校验语义闸 · FP-2 消费方兼容闸 · FP-5 CI/本地一致闸）。
2. `docs/tasks/close/close_ci_specwave_pin_align_20261017.md` §四·2 / §七·1（禁擅改史实的原始口径）。
3. `scripts/graph_yaml_to_json.py` 全文（:65-69 改造面 · json.dump 序列化参数）。
4. `docs/arch-browser/scripts/build_site.py` :545-607（消费方透传实证面）。
5. `docs/_tech_graph/shared/99_mermaid_protocol.md` :137（内容戳先例 · 方案 1 对齐锚点）。
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 前闸扫描）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 框定：graph.json 仅存两字段日期漂移（freeze_id 日期段 + generated_at），系 `graph_yaml_to_json.py:65-69` `datetime.now(UTC)`；md 面已是 sha256 内容戳，漂移面孤立 | false | — | spec-wave check 是否对 freeze_id 有隐性格式断言未实证（FP-1） |
| R1 | 证据：亲读生成源 :65-69 · 调用链 graph-compile.sh:58-59 / tech-graph.yml:33 · 消费方 build_site.py:558-559 透传 / app.js:55 展示 · 先例 99_mermaid_protocol.md:137 | false | — | 行号漂移（30 按实校正）；dist/site-data.json 存量快照对比口径 |
| R2 | 方案：三候选（内容 hash / env 注入 / git commit 时间）均可达字节级稳定；30 定案须满足「默认值确定性 + 骨架兼容」两约束；倾向内容 hash（与 md 先例同构 · 零环境依赖） | false | — | hash 序列化稳定性（sort_keys / ensure_ascii / 分隔符）需双跑实证 |
| R3 | 反例：freeze 校验语义破坏（FP-1）→ 保骨架或回 10；消费方兼容破坏（FP-2）→ 仅透传约束；env 方案 CI 未注入（FP-5）→ 默认值禁裸 now() | false | — | 三候选的取舍理由须 30 invoke 载明备 20/CLOSE 追溯 |
| R4 | 验收：TC-1 双跑 cmp / TC-2 骨架 grep + check OK / TC-3 消费方构建 + grep / TC-4 CI 绿 + CI/本地字节一致 / TC-5 datetime.now 清零断言 / TC-6 diff 白名单 | false | — | 无 |
| R5 | 收口：草稿交 20；闸全 pending 待维护者签；禁 30 | true | 改动面单一（一脚本两字段）· 证据锚点齐备 · 方案自由度已框定在三候选内，再轮无新信息 | 见 R0/R2/R3 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

graph.json 的 `freeze_id`（日期段 `%Y%m%d`）与 `generated_at` 由 `datetime.now(UTC)` 生成，致每次 graph-compile 产出漂移、diff 不稳定；2026-10-17 ci-pin 棒实证编译时 graph.json 被改写（20261014→20261017）后手工恢复零混入。图谱 md 面 `generated_at` 已是 sha256 内容戳，漂移面孤立在 graph.json 两字段。

### R1 · 证据收集

2026-10-17 亲读：生成源 `graph_yaml_to_json.py:65-69`；调用链 `graph-compile.sh:58-59` + `tech-graph.yml:33`（CI 同漂移）；消费方 `build_site.py:558-559` 纯透传、`web/app.js:55` 纯展示，无格式解析；先例 `99_mermaid_protocol.md:137` + 各图谱 md :4 `sha256-<16hex>` 实证内容戳钉法已在仓内落地。历史：FEEDBACK 1.5.2 K8 首录 freeze_id 按日滚动、1.10.0 R-graph-json 留档 P3。

### R2 · 方案生成

三候选均消漂移：(1) 内容 hash 派生——与 md 先例同构、零环境依赖，倾向项；(2) env 注入——须确定性默认值，禁裸 `now()` 回退；(3) git commit 时间——依赖 git 上下文，CI checkout 浅克隆风险须 30 实证。硬约束：`freeze_id` 骨架兼容 + 默认值确定性。30 定案并载明取舍理由；偏离三候选须先回 10。

### R3 · 反例与边界

freeze 校验语义（spec-wave check / schema_version=graph_v2）不可因改造破坏——30 先实证校验面无 freeze_id 格式断言；消费方仅透传展示故兼容约束弱，但新值须保持非空字符串；env 方案须防 CI/本地分裂；git 时间方案须防浅克隆无历史。漂移产出（graph.json 一次性落定 diff）属本 task 合法交付，其余图谱产出零卷入。

### R4 · 验收/可测性

TC-1 双跑字节断言（含 TZ 扰动）；TC-2 骨架 grep + check OK；TC-3 消费方构建 + grep 实证纯透传；TC-4 CI 绿 + CI/本地字节一致；TC-5 `datetime.now` 生成路径清零的防回归断言；TC-6 diff 白名单 + 钉版零 diff。

### R5 · 收口

草稿交 20-task-audit；人工闸全 pending 待维护者签；禁 30；未 commit。

### 自检结论（执行者）

- **30（2026-10-17 回填）**：方案定案候选①内容 hash 派生（理由见 30 invoke）；FP-1 先实证后定案（spec-wave@3.3.0 check 路径零 freeze 断言亲读实证）；TC-1/2/3/5/6 全 PASS 实证留痕 30 invoke（docs/harness/invokes/by-task/graph_json_freeze_date_pin/invoke_20261017_30_impl.md）；pytest 1843 passed，4 failed 环境归因实证与本 diff 零因果；PR #266 已建，TC-4 CI 绿态待 40 终核。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 初稿落盘（帽 10 · 闸 pending 待维护者签 · 禁 30 · 未 commit · 出处：close_ci_specwave_pin_align_20261017.md §四·2 / §七·1 另立案） |
