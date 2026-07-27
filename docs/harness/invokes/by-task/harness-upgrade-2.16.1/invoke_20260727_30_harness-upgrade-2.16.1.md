# Invoke：30（含 40）· harness-upgrade-2.16.1

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `harness-upgrade-2.16.1` |
| task_paths | `docs/tasks/active/task_harness_upgrade_2.16.1.md` |
| related_review_or_none | `docs/harness/reviews/task_harness_upgrade_2.16.1_audit_R1_20260727.md` |
| git_branch | `task/harness-upgrade-2.16.1` |
| created_utc_or_local | 2026-07-27 |
| notes | 维护者 30 Prompt：钉到 @cyning/harness@2.16.1 + 过程可观测冒烟；不 push/PR |

---

## 可复制 Prompt 快照

```text
upgrade --yes（无 --ide）；manifest→2.16.1；冒烟 check / status --json / timeline --json / status --check；
纪律层 commit；不做 P3b / 强制 hook / 业务改码。
```

---

## 交付摘要

- **upgrade**：`npx @cyning/harness@2.16.1 upgrade --target . --yes` → exit 0 一把过（无 S5）
- **manifest**：`2.14.0` → `2.16.1`；五字段；preset=`fullstack-node-py`；ide=`cursor,claude,agents`（**未被裁**）
- **check**：已是最新 · exit 0
- **status --json（全局）**：`obs_status_list.v1` · exit 0
- **status --task --json**：`obs_status.v1` · `may_start_30=true` · exit 0
- **timeline --json**：`obs_timeline.v1` · WARN 无 HGM · exit 0（未 `--ingest`）
- **status --check**：绿路径 · exit 0（闸齐；非缺 R1 场景）
- **lifecycle/discipline show**：可用（勿传 `--target`）；gate-check exit 0
- **pytest**：环境缺 `asyncpg`，conftest 加载失败 → **仅报告**，未改业务
- **摩擦**：upstream 2.16.1 sync 将 FRAGMENT/`30-execute`/`TEMPLATE_30`/`AGENTS` harness 段中的 **pre-30 文案**与 **`l1/01_modules`** 冲成产品默认 `01_struct`；已按 2.14 惯例写回本仓 overlay（净 diff 无这些文件）
- **下一棒**：维护者审 commit；可选 PR；web 升级另开；P3b 另 task

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-27 | upgrade + 过程可观测冒烟 + 纪律层 commit |
