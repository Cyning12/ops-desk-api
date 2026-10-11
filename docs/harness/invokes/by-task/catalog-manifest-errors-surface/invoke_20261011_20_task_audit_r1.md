# Invoke：20-task-audit · catalog-manifest-errors-surface（R1 书面审 task 草案）

| 字段 | 值 |
|---|---|
| hat_id | 20-task-audit |
| task_slug | catalog-manifest-errors-surface |
| invoke_slug | catalog-manifest-errors-surface |
| git_branch | `task/tool-catalog-page`（既有 · 勿切遵守 · 并行棒同分支 · 仅 add 本帽两文件） |
| upstream | 棒令：锚点核真（manifest.py:200/:102-105/:145-147 · __init__.py:110 · capability.py:99 · visibility.py:126/:38-41）+ N4 裁定理由 + 契约七条/TC1-TC5 可机断 + lint 复跑 |
| 交付物 | docs/audits/task-review/20261011_catalog-manifest-errors-surface_r1.md（裁定 PASS-WITH-NITS · NIT-1~3 照登） |
| lint | `npx spec-wave task lint --file` 复跑 **PASS** |
| 维护者签收栏 | **pending · 未代签**（三闸全 pending · 本审查文落盘即 HG-AUDIT-R1 前置交付 · 维护者签后方 approved） |

## 裁定摘要

**PASS-WITH-NITS**：锚点 14 组全亲读核真（码面 13 组 + 文献面 SPEC/R1 逐字）；N4 落点 A（catalog summary 面增 manifest_errors/manifest_error_details · 弃 B 扩 meta 面）理由链闭合——SPEC :78 首选语序 + meta 双消费方（admin/capability.py:99 /runtime）爆炸半径 + 单端点 diff + 断言单点机断；钉死契约七条与 TC1-TC5 全可机断（TC1 故障注入红测先行双钉在案）。

## NIT 照登（非阻塞 · 退 10 修订可选）

- NIT-1：契约 4 引「SPEC 纪律 #3/#6」无 #6（纪律仅 5 条 · SPEC :49-55）→ 实指 #3+FP-6。
- NIT-2：B1 表 test_capability_manifest_http.py:413-435 → 失败域隔离用例实起 :409，建议 :409-435。
- NIT-3（观察）：「:331/:354 钉键集」实为逐键值断言非键集相等断言；弃 B 主理由（双端点面）独立成立，裁定不受影响。

## 下一棒

维护者签 HG-TASK-DRAFT → HG-AUDIT-R1（本文前置交付）→ 30（TC1 故障注入红测先行再实现 · 故障记录结构细节 30 钉并留痕）。

| 日期 | 说明 |
|---|---|
| 2026-10-11 | 20 R1 落盘：PASS-WITH-NITS · 锚点全核真 · N4 裁定成立 · NIT-1~3 · lint PASS · 未代签闸 |
