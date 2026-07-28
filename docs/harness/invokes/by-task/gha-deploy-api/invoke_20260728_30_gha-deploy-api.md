# Invoke：30（含 40）· gha-deploy-api

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `gha-deploy-api` |
| task_paths | `docs/tasks/active/task_gha_deploy_api.md` |
| related_review_or_none | `docs/harness/reviews/task_gha_deploy_api_audit_R1_20260728.md` |
| git_branch | `task/gha-deploy-api` |
| created_utc_or_local | 2026-07-28 |
| notes | PR #17 合入后 30；对齐 web deploy-web；C1–C3 |

---

## GATE_VERIFY 摘要

三闸 approved · R1 签收 · VERIFY PASS · 可开工

---

## 交付摘要

- **去 probe**：`app/main.py` / `tests/test_health.py`；`task_health_temp_probe` → done/
- **workflow**：`.github/workflows/deploy-api.yml`（master push + dispatch；rsync api；`up -d --build api`；health 轮询）
- **文档**：`docs/deployment/gha-api-deploy.md` + README
- **pytest**：`tests/test_health.py` 绿
- **下一棒**：push + PR；维护者 Secrets / docker 组 / chown → `workflow_dispatch`

---

## 维护者首次验收清单

1. `gh secret set`：`DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_SSH_KEY`（可复用 web）
2. `DEPLOY_USER` 入 docker 组（或 sudoers）
3. `sudo chown -R ubuntu:ubuntu /opt/ops-desk/api`（若尚不可写）
4. Actions → deploy-api → Run workflow
5. `ssh … 'curl -fsS http://127.0.0.1:8000/health'` → 无 `probe`

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 实现 deploy-api + 去 probe |
