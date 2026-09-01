# Task：Host C3 · 受控 task 写盘（task writer）

> **状态**：active  
> **类型**：Host 沟通轨实现 / 受控写盘  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](../../spec/agent-infra/06_host_comms_boundary_spec_v0.md)（**signed** · #111）§5（产物路径）· §6（闸纪律 · C3 前置人确认）· §10（C3 行）  
> **前置**：C1 CLOSE · [`task_host_harness_cli_capability`](../done/task_host_harness_cli_capability.md) · [#114](https://github.com/Cyning12/ops-desk-api/pull/114)；C2 CLOSE · [`task_host_comms_prompt_pack`](../done/task_host_comms_prompt_pack.md) · [#116](https://github.com/Cyning12/ops-desk-api/pull/116)  
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
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C 轨串行：C0 ✓ → C1 ✓ → C2 ✓ → **C3**；C4 跨仓 web 可在本波 CLOSE 后并行（仅 web 侧） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | pending | 30 | 待 **20-task-audit** R1 落盘后 00 代签 |
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

- [ ] allowlist：仅三目录可写；`app/`/`tests/`/SPEC/图谱/逃逸路径（`../` · 绝对路径）全部拒绝（参数化断言）  
- [ ] dry-run 默认：`confirmed=False` → 返回 WritePlan + diff 预览且 **目标文件不存在**（断言未落盘）  
- [ ] 人确认：`confirmed=True` → 文件落盘且内容与 content 一致  
- [ ] 禁代签机械挡：content 人工闸节含 `HG-...` `approved` → `invalid_content` 拒绝（断言）  
- [ ] 结构自检：缺 Harness 元信息表/人工闸节/验收节 → 拒绝（断言）  
- [ ] 文件名：task 须 `task_<kebab-slug>.md` · invoke 须 `invoke_*.md` · kind/目录错配拒绝（断言）  
- [ ] overwrite：目标已存在且未显式 overwrite → 拒绝；dry-run diff 含差异  
- [ ] 不进 Gateway registry/manifest（grep/AST 断言 `task_writer` 未被 register）· SPEC §7 白名单零变更  
- [ ] `01_modules.md` capability 行备注；若增 `implementedBy` → G-L2 同步  
- [ ] `ruff check` 触及路径绿；pytest 相关绿；`./scripts/graph-compile.sh` exit 0  
- [ ] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

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

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C2 CLOSE（#116/#117）后起草 C3；钉 slug=`host-comms-task-writer`；落点=capability 包内纯服务（非 Gateway Capability · 避免新增一级模块/白名单变更）；allowlist 三目录 · dry-run 默认 · 人确认落盘 · 禁代签机械挡 · 不覆盖默认 |
