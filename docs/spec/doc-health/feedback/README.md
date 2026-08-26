# FEEDBACK · doc-health / CLOSE 试点（ops-desk-api → kit）

> **用途**：在本仓验证 **dsh-coding-kit** 新版本（CLOSE · Hub · dry-run 文案 · PR 闸 · 裸 SPEC warn 等）时，把可复现摩擦落盘，便于与 kit 维护者沟通。  
> **不是**：业务 bug 主轨（业务仍走 issues/tasks）；本目录专盯 **docs-ops / CLOSE 契约**。

---

## 怎么用

1. 复制 [`_TEMPLATE.md`](./_TEMPLATE.md) → `YYYY-MM-DD_<kit-version>_<short-topic>.md`  
2. 填：kit 版本 · 命令 · 期望 vs 实际 · 是否挡关账 · 建议  
3. 需要改闸时：在 kit 开 issue/PR，链回本文件路径  
4. 在本表追加一行

---

## 日志表

| 日期 | 文件 | kit 版本 | 主题 | 状态 |
|------|------|----------|------|------|
| 2026-08-26 | [`2026-08-26_1.7.1_upgrade-no-prompt-sync.md`](./2026-08-26_1.7.1_upgrade-no-prompt-sync.md) | 1.7.1 | upgrade 不落地 `00-orchestrator.md`；幂等刷新 `upgraded_at` | open |

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-08-26 | 建 FEEDBACK 轨 |
| 2026-08-26 | 登记 1.7.1 upgrade 未 sync 00 条文 |
