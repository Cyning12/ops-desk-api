# Invoke：30（含 40）· api-tech-graph-ci

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `api-tech-graph-ci` |
| task_paths | `docs/tasks/active/task_api_tech_graph_ci.md` |
| related_review_or_none | `docs/harness/reviews/task_api_tech_graph_ci_audit_R1_20260727.md` |
| git_branch | `task/api-tech-graph-ci` |
| created_utc_or_local | 2026-07-27 |
| notes | 维护者 30 Prompt：补 tech-graph CI；manifest 已 2.16.1 跳过 upgrade；默认开 PR |

---

## 可复制 Prompt 快照

```text
补 .github/workflows/tech-graph.yml（对照 web 金样：setup-node package-manager-cache:false + PyYAML + graph-compile）；
核对 pytest 触发与默认分支 master；跳过 upgrade；task/R1/invoke；冒烟后 commit + push + PR。
不做：web/ios、产品仓回灌、业务 Python、强制 pre-commit、P3b。
```

---

## 交付摘要

- **upgrade**：跳过（`.cyning-harness/manifest.json` 已 `2.16.1`）
- **tech-graph.yml**：对照 web 金样；`package-manager-cache: false`；PyYAML；`./scripts/graph-compile.sh`；`on: pull_request` + `push` → `master`
- **pytest.yml**：默认分支已是 `master`，触发未改
- **graph-compile**：exit 0；生成物 timestamp 噪声已还原，未入 commit
- **verify**：PASS · exit 0
- **status --check**：exit 0 · `may_start_30=true`
- **pytest**：`87 passed`（可选冒烟，环境可用）
- **下一棒**：push + PR；交还 00

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-27 | 补 api tech-graph CI + 冒烟 + 开 PR |
