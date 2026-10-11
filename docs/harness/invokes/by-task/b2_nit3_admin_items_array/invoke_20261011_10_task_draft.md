# invoke：10-task 起草（b2_nit3_admin_items_array · 2026-10-11）

> **帽位**：10-task（任务需求分析 · 只起草文档 · 零实现码改动）
> **task**：`docs/tasks/active/task_b2_nit3_admin_items_array.md`（本帽产出 · draft）
> **worktree/分支**：`../ops-desk-api-worktrees/t-b2-nit3-admin-items-array` · `task/b2-nit3-admin-items-array`（base master 286d825 · 主仓 checkout 他棒占用未动）

## 立项令

交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 4 项：「B2 NIT-3 / admin items 全字段数组（close 档后续建议四条照录）」。

## 输入真读清单（本帽亲读 · 非凭记忆）

| 文档/码面 | 读取要点 |
|---|---|
| PROMPT_00_spec-campaign-handoff_20261011.md | §2.2 第 4 项立项令 · §4 机读纪律坑（lint 契约 / verify 重定向取真码 / invoke 目录禁 heredoc） |
| docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md | §4 偏差 2（NIT-3 原文：tests/test_capability_manifest.py:331/:354 逐键值断言非键集相等 · 照登不阻）· §7 后续建议四条照录（第 2/3 条入范围 · 第 1/4 条入非范围） |
| docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md | §2 B2 :75-78（items 字段族 14 键 + status 三态钉案）· §3 非范围 · §5 FP-4/FP-5/FP-6 · 纪律 #2/#3/#4 |
| app/ops/admin/capability.py:164-219 | catalog 现状：`{filter, principal, visible_ids, **summary, manifest_errors, manifest_error_details}` · :214 visible_ids 裸 id 列表 · :179-181 baseline_filter 构造 |
| app/ops/capability/registry.py:85-91 / :112-121 | list_specs 无 filter 回全量在册（含 disabled）· `_match_filter` :120-121 disabled 首判——items 数据源裁定关键实证 |
| app/ops/capability/visibility.py:38-49/:93-151 | 词表 VISIBILITY_REASON_TEXTS · check_visible · evaluate_visibility（status/visibility_reason 唯一真源） |
| app/ops/capability/types.py:77-130 | CapabilitySpec 字段族（id/kind/description/when_to_use/when_not_to_use/tags/risk_level/side_effect/enabled/tenant_scoped/reversible/execution_type 等 · adapter/args_schema 显式排除面） |
| app/ops/capability/manifest.py:102-105/:150-152 | `_LAST_META` 两键 + get_capability_manifest_metadata（NIT-3 被测面 · 钉死零改动） |
| app/ops/capability_mine.py:35-51 | B1 九键投影先例（project_capability · 本 task 14 键族扩面参照） |
| tests/test_capability_manifest.py:311-356 | NIT-3 锚点：:331-333/:354-356 meta 逐键值断言无键集相等 |
| docs/tasks/done/task_catalog_manifest_errors_surface.md | 结构先例（元信息表 / 闸表 4 列 / 钉死契约 / 思考轮控制表 / B1 旧测影响面） |

## 关键裁定（R2 · 留痕）

**items 数据源裁 S1（全量在册 · 无 filter）**，弃 S2（蹭 cap_filter 快照）：registry.py:120-121 `_match_filter` 首判 `if not spec.enabled: return False`，catalog 默认 `baseline_filter(node_role="admin_preview")`（admin/capability.py:179-181）——S2 下 disabled 条目永不出现，SPEC :77 status 三态缺一角；且 SPEC :75 钉死「每个在册 capability 一条（不止可见集）」，被 kinds/deny_write 场景裁剪的在册条目亦须出 items。query 的 baseline/filter 参数只影响既有 visible_ids/summary（零 diff），不影响 items 覆盖集。状态判定仍复用 check_visible 单源（纪律 #3 不破）。

## 产出

- task 文件：`docs/tasks/active/task_b2_nit3_admin_items_array.md`（钉死契约七条 · TC1–TC6 · failure_paths 闸行+七行四列表 · B1 旧测影响面五文件 · 思考轮 R0–R5 early_stop at R5）
- 人工闸表四闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 **pending（未代签）** · HG-PILOT-OPSDESK-GLAYER n/a
- graph_change_layer 预判 `n/a`（既有端点响应增键 + 纯测试断言强化 · modules.md :38 admin 行既有备注覆盖 · 条件回写义务在案）
- review_hat `20` · required_invoke_hats `10,20,30,40` · invoke_retention_profile `default`

## 门禁实证（重定向取真码）

- `npx --yes spec-wave@3.2.0 task lint --file docs/tasks/active/task_b2_nit3_admin_items_array.md > /tmp/lint_b2_nit3_admin_items_array.log 2>&1; echo EXIT=$?` → **EXIT=0 · LINT: PASS**（W3 自检结论占位符提醒 · draft 期合法 · close 前须回填）
- `npx --yes spec-wave@3.2.0 verify --target . --task docs/tasks/active/task_b2_nit3_admin_items_array.md > /tmp/verify_b2_nit3_admin_items_array.log 2>&1; echo EXIT=$?` → **EXIT=2 · VERIFY: BLOCKED**——仅因新 draft 三闸 pending（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）属**正确语义**（未代签）；零解析告警 · 闸表 4 列 status 纯 pending 解析正常
- verify 后 `git status --short`：仅本 task 两件新档（task 文件 + 本 invoke）· **零再生噪音**

## 遗留

- 投影函数落点细节（admin/capability.py 模块内私有函数 vs 独立投影点）与 visibility_reason 非 denied 条目形态（None/缺省）刻意开放留 30 钉。
- HG-AUDIT-R1 前需 20-task-audit R1 落盘；verify EXIT=2（三闸 pending）为正确语义。
