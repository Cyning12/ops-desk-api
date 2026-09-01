# Task：Host C3 · 受控 task 写盘（task writer）

> **状态**：completed（2026-09-01 CLOSE · PR [#118](https://github.com/Cyning12/ops-desk-api/pull/118) MERGED）  
> **类型**：Host 沟通轨实现 / 受控写盘  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](../../spec/agent-infra/06_host_comms_boundary_spec_v0.md)（**signed** · #111）§5（产物路径）· §6（闸纪律 · C3 前置人确认）· §10（C3 行）  
> **前置**：C1 CLOSE · [`task_host_harness_cli_capability`](./task_host_harness_cli_capability.md) · [#114](https://github.com/Cyning12/ops-desk-api/pull/114)；C2 CLOSE · [`task_host_comms_prompt_pack`](./task_host_comms_prompt_pack.md) · [#116](https://github.com/Cyning12/ops-desk-api/pull/116)  
> **分支**：`task/host-comms-task-writer`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **无关**：C4 UI · 接 LLM/真 comms 会话 · Gateway 白名单变更（SPEC §7 修订才准）· 改产品 lg-rag/Chat · 真跑 npx

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `host-comms-task-writer` |
| **git_branch** | `task/host-comms-task-writer` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | tmp_path 沙箱纯函数测：allowlist 命中/拒绝（`app/` · `tests/` · SPEC 正文 · 图谱 yaml → 拒绝）；dry-run 默认不落盘断言；confirmed=True 落盘断言；禁代签内容（人工闸表 approved 字样）拒绝断言；slug/文件名模式校验；不真跑 npx |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（capability 行备注） |
| **graph_delta_note** | 写盘服务落 `app/ops/capability/` 既有 glob；**不新增一级模块**；若增 `implementedBy` → 同步 G-L2 indexes |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 SPEC 06 §5/§6 + 本 task；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `n/a` |
| **close_pr_policy** | `required` |
| **related_pr** | `#118` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C 轨串行：C0 ✓ → C1 ✓ → C2 ✓ → **C3**；C4 跨仓 web 可在本波 CLOSE 后并行（仅 web 侧） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | approved | 30 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** · 见 `docs/harness/reviews/task_host_comms_task_writer_audit_R1_20260901.md`（R1 pass · 内容零阻塞） |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块（落 capability 行）· **00 代签** |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`host-comms-task-writer`** |
| **落点** | `app/ops/capability/task_writer.py`（Host 受控写盘服务 · **纯函数/服务层** · **不是** Gateway Capability · **不进** registry/manifest · 不触发 SPEC §7 白名单变更）。若 20 认为须新增一级模块（comms/host）→ **退回 00 升级维护者明示**（本 Prompt 未授权新增一级模块） |
| **API 形态** | `plan_task_write(slug, content, *, kind, repo_root) -> WritePlan`（路径解析 + allowlist 校验 + dry-run diff/预览）· `apply_task_write(plan, *, confirmed: bool = False)`（confirmed=False → **不落盘** 返回 dry-run 结果；confirmed=True 即人确认后 → 写盘）。**无 HTTP 路由**（接线留 C4/Host） |
| **allowlist** | **仅**：`docs/tasks/active/` · `docs/tasks/draft/`（不存在可创建）· `docs/harness/invokes/by-task/<slug>/`。其佘一律拒绝（`app/` 永久 · `tests/` · 图谱 yaml · SPEC 正文 · 任意逃逸） |
| **文件名约束** | task 文件 `task_<slug>.md`（slug kebab-case 校验）；invoke 文件 `invoke_*.md`；kind 与目录不匹配 → 拒绝 |
| **禁代签机械挡** | content 含人工闸节且把 `HG-*` status 写为 `approved`（非模板占位）→ **拒绝写入**（`invalid_content`）；人签只能由人/00 授权流程落（SPEC §6） |
| **结构自检** | 写盘前最小结构校验（Harness 元信息表 · 人工闸节 · 验收节存在）；**不真跑 npx lint**（Policy 默认关 · CI 不断网） |
| **overwrite** | 默认 **不覆盖**已存在文件（须显式 `overwrite=True` 且仍走 confirmed）；dry-run diff 含新旧差异 |
| **模块** | 不新增一级模块 |

---

## 范围

1. `task_writer.py`：`plan_task_write` + `apply_task_write`（allowlist · dry-run 默认 · 人确认落盘 · 禁代签机械挡 · 结构自检 · 文件名/slug 校验 · overwrite 保护）  
2. api 单测（tmp_path 沙箱 · 全 mock 文件系统语义 · 不真跑 npx）  
3. 图谱 capability 行备注；若增 `implementedBy` → G-L2 indexes  
4. ruff + pytest + graph-compile

## 非范围

- **C4** `/obs` UI / 发起沟通入口（跨仓 web 另 task）  
- 接 LLM / 接 C2 pack 装配调用（本波纯写盘服务；串线另议）  
- Gateway 注册新 capability（SPEC §7 白名单仅三条 · 新增须 SPEC 修订）  
- 真跑 `npx dsh-coding-kit`（CI 不断网）  
- 改 SPEC 正文 / 图谱 yaml / `app/` 业务码 的写盘能力（永久禁写）  
- 删文件 / 移动文件（git mv 类操作）· 写 docs/tasks/done/（归档走 00 CLOSE 流程，非 comms 写盘）

---

## 验收标准

- [x] allowlist：仅三目录可写；`app/`/`tests/`/SPEC/图谱/逃逸路径（`../` · 绝对路径）全部拒绝（参数化断言）  
- [x] dry-run 默认：`confirmed=False` → 返回 WritePlan + diff 预览且 **目标文件不存在**（断言未落盘）  
- [x] 人确认：`confirmed=True` → 文件落盘且内容与 content 一致  
- [x] 禁代签机械挡：content 人工闸节含 `HG-...` `approved` → `invalid_content` 拒绝（断言）  
- [x] 结构自检：缺 Harness 元信息表/人工闸节/验收节 → 拒绝（断言）  
- [x] 文件名：task 须 `task_<kebab-slug>.md` · invoke 须 `invoke_*.md` · kind/目录错配拒绝（断言）  
- [x] overwrite：目标已存在且未显式 overwrite → 拒绝；dry-run diff 含差异  
- [x] 不进 Gateway registry/manifest（grep/AST 断言 `task_writer` 未被 register）· SPEC §7 白名单零变更  
- [x] 原子写：写盘异常不留半截文件（先写临时文件再 rename 语义断言 · failure_paths 兜底）  
- [x] allowlist 目录可创建：`docs/tasks/draft/` 不存在时 mkdir（parents）创建；非 allowlist 目录一律不创建  
- [x] `01_modules.md` capability 行备注；若增 `implementedBy` → G-L2 同步  
- [x] `ruff check` 触及路径绿；pytest 相关绿；`./scripts/graph-compile.sh` exit 0  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 路径越 allowlist | 拒绝（`path_not_allowed`）· 不落盘 | 否 | 校验错误 |
| 未人确认（confirmed=False） | dry-run 结果 · 不落盘 | 确认后重试 | diff 预览 |
| 禁代签内容 | `invalid_content` 拒绝 | 否（须人去签） | 校验错误 |
| 结构自检失败 | `invalid_structure` 拒绝 · 指出缺节 | 修内容后重试 | 校验错误 |
| 目标已存在未 overwrite | `exists` 拒绝 | 显式 overwrite+confirmed | 校验错误 |
| 写盘 IO 失败 | 异常上抛 · 不留半截文件（先写临时文件再 rename） | 是 | capability 错误 |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md` §5 · §6（signed）  
3. 只读参考：`app/ops/capability/harness_cli.py`（C1 风格参照）· `app/ops/prompts/packs.py`（C2）  
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
5. `docs/_tech_graph/l1/01_modules.md`（capability 行）

---

### 自检结论

> **10-task** · 2026-09-01 · 分支 `task/host-comms-task-writer` · docs-only 本帽（不改 `app/` / `tests/`）· HG-AUDIT-R1 保持 **pending**（本帽不签发）

**现网事实核对**（只读 `app/ops/capability/` · `docs/_tech_graph/l1/01_modules.md` · `docs/tasks/` · `docs/harness/invokes/by-task/` · SPEC 06 · 结论：现网与 task 陈述**全部一致**，零事实修正）

| 核对项 | 现网事实 | 结果 |
|---|---|---|
| 落点包 `app/ops/capability/` | 包存在（`gateway.py` · `registry.py` · `manifest.py` · `policy.py` · `harness_cli.py` 等）；C1 风格参照 `harness_cli.py` 在（docstring 钉死项 + 纯模块常量风格） | ✅ 00 定夺落点 `app/ops/capability/task_writer.py` 可落；**纯服务不进 registry/manifest** 与 C1（`gateway.register`）形态差异已由 00 定夺明示 |
| 图谱 capability 行 glob | `docs/_tech_graph/l1/01_modules.md` L26 `capability` 行 path glob = `app/ops/capability/**` | ✅ `task_writer.py` 落既有 glob · **不新增一级模块** · graph_delta 仅行备注属实 |
| allowlist 三目录 | `docs/tasks/active/` ✓ 存在；`docs/tasks/draft/` **不存在**（`docs/tasks/` 仅 `_views/active/deferred/done/` + `PRIORITY_DEFERRED.md`）；`docs/harness/invokes/by-task/<slug>/` 结构在（86 个 task 目录 · 含本 slug） | ✅ 00 定夺「draft/ 不存在可创建」与现网一致；invokes 目录结构匹配 |
| 前置 C1/C2 CLOSE | `docs/tasks/done/task_host_harness_cli_capability.md` ✓ · `docs/tasks/done/task_host_comms_prompt_pack.md` ✓ 均在 done/ | ✅ task 前置声明属实（#114 / #116） |
| 必读列表引用 | SPEC `06_host_comms_boundary_spec_v0.md` ✓（§5/§6/§7/§10/§15 均在）· `app/ops/prompts/packs.py` ✓ · `CODING_BACKEND_L2_v1_zh.md` ✓ | ✅ 全部引用路径存在 |
| 本 slug invoke 目录 | `docs/harness/invokes/by-task/host-comms-task-writer/invoke_20260901_00_host-comms-task-writer.md` ✓ 已落盘 | ✅ pre-30 invoke 链（00 → 10）成立 |

**00 定夺范围实质**：**零改动**（slug / 落点纯服务非 Gateway Capability · 不进 registry·manifest / API 形态 plan+apply · dry-run 默认 confirmed=False / allowlist 三目录 / 文件名·slug 校验 / 禁代签机械挡 / 结构自检不真跑 npx / overwrite 默认拒 / 无 HTTP 路由 / 不新增一级模块 · 须增则退回 00 —— 全部保留）；仅补 2 条验收钩（原子写不留半截文件 · allowlist 目录可创建——均为 failure_paths/00 定夺已钉行为的可检验化，非范围变更）。

**lint 与禁区**

- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_task_writer.md` → **PASS**（exit 0 · **W4 合法**：无思考轮节 · 思考轮由 SPEC 06 §15「思考轮控制（10-spec 回填）」承载，本 task 为 SPEC 落地执行波）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**
- [x] `app/` · `tests/` 零改动；人工闸状态未改（HG-AUDIT-R1 仍 pending · HG-TASK-DRAFT / HG-GRAPH-MODULES approved 未动）
- [x] invoke 落盘：`docs/harness/invokes/by-task/host-comms-task-writer/invoke_20260901_10_task_host-comms-task-writer.md`（hat_id=10-task）
- 下一棒：**20-task-audit** R1 落盘 → 00 代签 HG-AUDIT-R1 → 30 开工

### 自检结论（执行者）

> **30+40** · 2026-09-01 · 分支 `task/host-comms-task-writer`（未切换 · 未 push · 未开 PR）

**GATE_VERIFY**：三闸 approved（task 表真值）· `npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_host_comms_task_writer.md` → **VERIFY: PASS**（exit 0 · 开工前与收尾各跑一次均 PASS）

**自检命令逐条**

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit@1.10.0 verify --target . --task <task>` | 0 | PASS（×2：开工前 + 收尾） |
| `ruff check app/ops/capability/task_writer.py tests/test_capability_task_writer.py` | 0 | All checks passed（全量 `ruff check app tests` exit 1 = 2 处**既有**问题 rag/tokenizer UP035 · test_rag_chunker I001，与 C2 记录同款 · git 未触及 · 按 P-07 不顺手改） |
| `pytest tests/test_capability_task_writer.py -q` | 0 | **48 passed** |
| `DATABASE_URL=postgresql+asyncpg://127.0.0.1:1/invalid pytest tests -q --tb=short`（CI 等价） | 0 | **591 passed · 39 skipped**（基线 543 + 新增 48 · 旧测零回归） |
| `./scripts/graph-compile.sh` | 0 | 9 graphs OK · 生成物 graph.json 仅 generated_at 刷新 |
| `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` | 0 | PASS（issues: 0） |

**R1 非阻塞 5 条处置明细**

| # | 处置 |
|---|---|
| ①「非模板占位」宁严勿宽 | **按宁严实现**：人工闸节内任何含 `HG-` 且含 `approved` 词的行一律 `invalid_content` 拒绝（大小写不敏感 · 说明列出现同样拒 · 无占位例外）；00 代签不经 comms 写盘，严挡不误伤合法流程。测试：大小写/说明列/overwrite 注入 approved 侧路均有断言；闸节外 approved 字样不误伤有断言 |
| ② apply 信任边界 | **双保险**：apply 复跑全部校验（kind↔路径一致性 · allowlist realpath · 结构 · 禁代签 · exists）+ WritePlan 携带 sha256 校验摘要（kind/slug/repo_root/rel_path/abs_path/content/overwrite）；手工构造或篡改 → `plan_tampered`。测试：非 WritePlan 拒 · 篡改字段拒 · 手造 plan 拒 · 合法 checksum 构造 plan 仍被内容关拦（invalid_content / invalid_structure / path_not_allowed） |
| ③ realpath 前缀判定 | 目标 `.resolve()` 后对**字面拼接**的 allowlist 根做 `is_relative_to` 判定——allowlist 目录被 symlink 替换时 resolved 目标与字面根不匹配 → `path_not_allowed`；slug kebab 正则天然排除 `/`/`..`/反斜杠/绝对路径。测试：symlink 替身逃逸断言 + 11 种注入 slug 参数化断言 |
| ④ 文件名/kind 错配归并 | 目录由 kind+slug 唯一推导（task → `task_<slug>.md` · invoke → `invoke_<slug>.md`）；apply 复跑推导比对，kind 与路径错配 → `path_not_allowed` 归并（与 failure_paths 同形态）；slug/kind 非法 → `invalid_args`。测试：错配构造 plan 断言 + 文件名模式断言 |
| ⑤ draft/ 新增任务态目录 | mkdir parents **仅**在 confirmed=True 落盘时、目标目录已过 allowlist 判定后执行；dry-run/被拒零目录副作用。测试：draft/invokes 嵌套目录确认落盘创建 · dry-run 不创建 · 非 allowlist 目录（done/ 等）永不创建 |

**禁区核对**：无 HTTP 路由 · 未 import/call gateway registry manifest（AST 断言）· registry/defaults/manifest/builtin.yaml 零 `task_writer` 引用（grep 断言）· 活注册表无 task_writer id · SPEC §7 白名单零变更（SPEC 文件零 diff）· 无删/移动文件能力 · 不写 done/ · 未签 human_gate · 未切分支/未 push/未开 PR

**已知未测项**：`repo_root` 缺省解析（parents[3]）在部署/打包环境的路径有效性（本波纯服务无部署接线 · 测试全走显式 tmp_path）；invoke 文件名为推导式 `invoke_<slug>.md`（真实 invoke 命名含日期/帽由 C4/Host 接线层决定 · glob 约束已断言）；禁代签挡对无人工闸节 invoke 内容不生效（invoke 不设人工闸节 · task 类由结构自检封死侧路）。

**下一棒**：00 CLOSE（本帽不 CLOSE）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C2 CLOSE（#116/#117）后起草 C3；钉 slug=`host-comms-task-writer`；落点=capability 包内纯服务（非 Gateway Capability · 避免新增一级模块/白名单变更）；allowlist 三目录 · dry-run 默认 · 人确认落盘 · 禁代签机械挡 · 不覆盖默认 |
| 2026-09-01 | **10-task**：现网核对全一致（capability 包/harness_cli.py ✓ · 图谱 capability 行 glob ✓ · draft/ 不存在 ✓ · C1/C2 done ✓ · 必读引用全在 ✓）零事实修正；补验收钩 2 条（原子写不留半截文件 · allowlist 目录可创建——已钉行为可检验化）；补 `### 自检结论`（W4 合法：思考轮由 SPEC 06 §15 承载）；invoke 落盘；00 定夺实质零改 · HG-AUDIT-R1 保持 pending · 下一棒 20-task-audit |
| 2026-09-01 | **20** R1 **pass**（内容零阻塞；写盘层无可绕过禁代签挡/allowlist 路径确认；非阻塞 5 条已录审查文）· **00** 代签 `HG-AUDIT-R1` → approved；可派 30 |
| 2026-09-01 | **30+40**：实现 `app/ops/capability/task_writer.py`（plan/apply · allowlist realpath · dry-run 默认 · 禁代签宁严挡 · 结构自检 · overwrite 默认拒 · 原子写 · WritePlan sha256 防伪造）+ `tests/test_capability_task_writer.py` 48 用例全绿；R1 非阻塞 5 条逐项处置；图谱 capability 行备注 + 人签记录行；验收 13 条全勾；自检全绿（verify ×2 · ruff 触及路径 · pytest 591 passed 零回归 · graph-compile · lint-wiki-delta）；**不 CLOSE（留给 00）** |
| 2026-09-01 | **00 CLOSE**：PR [#118](https://github.com/Cyning12/ops-desk-api/pull/118) MERGED（CI 三绿）；无 Alembic；00 独立复跑 591 passed / ruff 净；归档 done/ · Hub 补登 · CLOSE invoke 留档 |

---

30+40 交付完毕。00 关账复检：独立复跑 pytest CI 等价 **591 passed / 39 skipped** · ruff 触及路径净 · PR #118 CI 三绿后 squash MERGED。

---

## 关账（CLOSE）

| 项 | 值 |
|---|---|
| PR | [#118](https://github.com/Cyning12/ops-desk-api/pull/118) **MERGED** 2026-09-01 |
| 交付 | `app/ops/capability/task_writer.py`（allowlist 三目录 · dry-run 默认 · 人确认落盘 · 禁代签机械挡 · WritePlan 防伪造 · 原子写）+ 48 用例 |
| 生产 | 无 Alembic · 无新路由 · 纯服务未接线（业务零影响） |
| 归档 | 2026-09-01 · 00 关账 · 维护者 Prompt 授权 |

### KPI

Task_KPI%: 100 · D1 范围钉死受控写盘纯服务 · D2 闸齐（三代签 + 20 R1 pass · 写盘层无绕径确认）· D3 过程档齐（invoke 10/00/30_40 + R1 审查）· D4 图谱 capability 行备注已随 #118 · D5 关账补登 2026-09-01
