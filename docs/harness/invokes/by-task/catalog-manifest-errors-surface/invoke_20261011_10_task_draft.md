# Invoke：10-task · catalog-manifest-errors-surface（B2 catalog 故障可见性 task 起草）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | catalog-manifest-errors-surface |
| invoke_slug | catalog-manifest-errors-surface |
| git_branch | `task/tool-catalog-page`（既有 · 勿切） |
| upstream | SPEC v0 §2 B2（docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md · HG-SPEC-SIGNOFF approved 2026-10-11）+ R1 N4 携带回填（docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md） |
| 交付物 | docs/tasks/active/task_catalog_manifest_errors_surface.md（钉死契约七条 + TC1–TC5 + 三闸 pending） |
| lint | `npx spec-wave task lint --file` PASS（首轮 E5 缺自检结论节 → 已补）· 结构对齐 docs/tasks/done/task_hitl_auto_resume_claim_race.md 先例（元信息表/人工闸表/锚点表/钉死契约/范围/failure_paths/B1 表/验收/思考轮控制） |
| 维护者签收栏 | **pending · 未代签**（三闸 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending） |

## 关键裁定（N4 携带回填 · 本 task 裁一）

**manifest_errors 落点裁 A：catalog 响应 summary 面顶层增 `manifest_errors`（计数）+ `manifest_error_details`（[{path,error}]）**。

- 弃选 B（扩 `get_capability_manifest_metadata` meta 面）：该 meta 被 `/runtime`（app/ops/admin/capability.py:99）同步消费，扩键 = 双端点响应面同动 + tests/test_capability_manifest.py:331/:354 断言牵连；落点 A 收敛 diff 于 catalog 单端点、与 visibility_* 平铺外形一致、故障注入单点机断。
- 共同前提：manifest.py 须新增模块级故障记录（现状 failed 集在 app/ops/capability/__init__.py:110 调用点即弃 · 仅 manifest.py:200 日志留存）。

## 实证锚点（亲读在案）

| 锚点 | 位置 |
|---|---|
| 故障日志唯一留存 | app/ops/capability/manifest.py:200 |
| meta 仅 version+count | app/ops/capability/manifest.py:102-105 · :145-147 |
| failed 集丢弃点 | app/ops/capability/__init__.py:110 |
| meta 消费方（弃 B 证据） | app/ops/admin/capability.py:99 |
| catalog 响应现状 | app/ops/admin/capability.py:163-214（R1 N1 修正锚点） |
| hidden reason 数据源 | app/ops/capability/visibility.py:126（词表 :38-41） |

## B1 旧测影响面（清点）

tests/test_admin_capability_observability.py（catalog 五测试 · :113 hidden 面）· tests/test_capability_manifest.py:331/:354（meta 钉死零 diff）· tests/test_capability_manifest_http.py:413-435（失败域隔离存续）· tests/test_multi_replica_dualproc.py:674-718（catalog 跨副本 parity）· tests/test_capability_visibility_and_receipts.py:135。

## 下一棒

20 R1（书面审 task 草案）→ 维护者签 HG-TASK-DRAFT → HG-AUDIT-R1 → 30（TC1 故障注入红测先行再实现）。

| 日期 | 说明 |
|---|---|
| 2026-10-11 | 10 首稿（骨架+全文一次落 · N4 裁 A 留痕 · 三闸 pending 未代签） |
