# Task：GHA 自动部署 api（对齐 web）+ 移除临时 health probe

> **状态**：completed  
> **类型**：CI/CD（workflow + 文档）+ 极小 API 面（去 probe）  
> **关联 SPEC**：`docs/spec/SPEC-gha-deploy-api_v1.md`（accepted · HG-SPEC-SIGNOFF approved）  
> **合入**：PR #18 · `978912a` · 2026-07-28  
> **生产验收**：deploy-api run `30327570930` success · health `{"status":"ok"}`（无 probe）  
> **关账**：CLOSE · 迁入 `docs/tasks/done/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `gha-deploy-api` |
| **git_branch** | `task/gha-deploy-api` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 无图谱变更；仅 CI workflow / 部署文档 / 去掉临时 `/health` probe |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 去 probe：`pytest tests/test_health.py` 必绿；deploy workflow：缺 Secrets 时失败信息可读；**不**在 CI runner 内强制真实 SSH 打生产（验收靠维护者 `workflow_dispatch`） |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task；00 代签双闸（基础设施 + SPEC 已签收）；对照 web-gha-deploy-frontend |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：无模块边界变更；仅 workflow/docs + 删 `/health` probe |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者：SPEC 签收后推进；00 派发 |
| **HG-AUDIT-R1** | approved | **30** | 00 兼 20：见 `docs/harness/reviews/task_gha_deploy_api_audit_R1_20260728.md` |

---

## 背景与目标

web 已合入 GHA `deploy-web`；api 仍靠本机 `deploy.sh --skip-web`。临时 `/health` probe（`20260728-a`）已验收，须同波删除。

**完成态**：

- [x] `GET /health` 恢复 `{"status":"ok"}`；更新 `tests/test_health.py`；归档 `task_health_temp_probe` → `done/`
- [x] `.github/workflows/deploy-api.yml`：`push`→`master` + `workflow_dispatch`；timeout ≥20min
- [x] Job：Secrets 门闩 → rsync api → SSH `up -d --build api`（C1）→ health 轮询
- [x] **不** reload Nginx（C2）；**不**每次 sudo chown（C3）
- [x] `docs/deployment/gha-api-deploy.md` + README 指针
- [x] commit → push → PR；维护者 Secrets 验收

---

## 验收标准

- [x] `pytest tests/test_health.py` 绿；无 `probe` 字段
- [x] workflow 与文档与 SPEC/C1–C3 一致
- [x] 缺 Secrets 时失败信息可读
- [x] 未改 `app/ops/**`
- [x] 合入后 deploy-api 绿；health 无 probe

---

## CLOSE

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **PR** | [#18](https://github.com/Cyning12/ops-desk-api/pull/18) MERGED |
| **生产** | run `30327570930` · `API_healthy` · `{"status":"ok"}` |
| **分支** | 已删 `task/gha-deploy-api` |
