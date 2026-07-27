# Invoke：30（含 40）· harness-upgrade-2.14.0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `harness-upgrade-2.14.0` |
| task_paths | `docs/tasks/active/task_harness_upgrade_2.14.0.md` |
| related_review_or_none | `docs/harness/reviews/task_harness_upgrade_2.14.0_audit_R1_20260727.md` |
| git_branch | `task/harness-upgrade-2.14.0` |
| created_utc_or_local | 2026-07-27 |
| notes | 用户告知 @cyning/harness@2.14.0 已发；本仓 upgrade + pre-30 dogfood |

---

## 可复制 Prompt 快照

```text
升级 api 至 2.14.0（upgrade --yes 无 --ide）；FRAGMENT 对齐 pre-30 并保留 l1/01_modules；
用 task_glayer_phase_alpha_api dogfood：有 10 → PASS；暂移 10 → BLOCK；恢复。
```

---

## 交付摘要

- **验证**：`harness check` 已是最新（2.14.0）
- **dogfood PASS**：`verify --task …/task_glayer_phase_alpha_api.md` → PASS · `invoke_pre30_ok=true` · required `[10]`
- **dogfood BLOCK**：移走 `invoke_*_10_*` → `VERIFY: BLOCKED · missing pre-30 invoke hats · 缺 10（已有 30,40）`；已恢复
- **变更路径**：`.cyning-harness/manifest.json` · prompts sync · FRAGMENT（l1/01_modules）· AGENTS harness 段补 pre-30
- **下一棒**：维护者 commit / PR；web 升级另议

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-27 | upgrade + dogfood 完成 |
