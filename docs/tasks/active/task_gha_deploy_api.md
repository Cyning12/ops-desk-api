# Task：GHA 自动部署 api（对齐 web）+ 移除临时 health probe

> **状态**：ready-for-merge  
> **类型**：CI/CD（workflow + 文档）+ 极小 API 面（去 probe）  
> **关联 SPEC**：`docs/spec/SPEC-gha-deploy-api_v1.md`（accepted · HG-SPEC-SIGNOFF approved）  
> **SPEC 审查**：`docs/harness/reviews/spec_gha-deploy-api_audit_R1_20260728.md`（C1–C3 已落盘）  
> **金样**：`../ops-desk-web/.github/workflows/deploy-web.yml` · `../ops-desk-web/docs/deployment/gha-frontend-deploy.md`  
> **应急**：`../ops-desk-workspace/deploy/deploy.sh --skip-web` 仍保留

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `gha-deploy-api` |
| **git_branch** | `task/gha-deploy-api` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 无图谱变更；仅 CI workflow / 部署文档 / 去掉临时 `/health` probe |
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
- [x] Job：Secrets 门闩 → rsync api（排除项对齐 `deploy.sh`；**禁止**触及 `/opt/ops-desk/web/`）→ SSH `up -d --build **api**`（C1；不重建 db；无 sudo 或按文档）→ curl `:8000/health` 轮询
- [x] **不** reload Nginx（C2）
- [x] **不**每次 sudo chown（C3）；文档写清一次性属主与 docker/sudo 择一
- [x] `docs/deployment/gha-api-deploy.md` + README 指针
- [ ] commit → push → PR；交付维护者 Secrets / 权限清单（Agent 不写私钥）

**不做**（摘自 SPEC §3）：改 `app/ops/**` 业务、改 deploy-web、搬 workspace deploy/、Registry CD、正式 version API、灰度

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| Secrets 未配 | deploy job 失败并提示缺项 + 文档路径 | 是 |
| SSH 拒连 | job 红；查 key / authorized_keys | 是 |
| api 目录不可写 | job 红；一次性 chown（C3） | 是（人） |
| 无 docker/sudo | job 红；按文档补权限 | 是（人） |
| compose 缺失 / build·alembic·health 失败 | job 红；查远端 logs | 是 |

---

## 验收标准

- [x] `pytest tests/test_health.py` 绿；无 `probe` 字段
- [x] workflow 文件与文档存在且与 SPEC/C1–C3 一致
- [x] 缺 Secrets 时失败信息可读
- [x] 未改 `app/ops/**`；未改 web dist 路径逻辑
- [ ] （维护者）Secrets+权限就绪后 `workflow_dispatch` 绿；`:8000/health` 无 probe

---

## 部署备注

合入后 **首次** 需维护者：配齐 Secrets（可复用 web key）、确认 docker 组或 sudoers、确认 `/opt/ops-desk/api` 可写，再用 Actions `workflow_dispatch` 验收。

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **probe** | 已删除；`/health` → `{"status":"ok"}` |
| **workflow** | `.github/workflows/deploy-api.yml` · C1 `up -d --build api` |
| **docs** | `docs/deployment/gha-api-deploy.md` + README 指针 |
| **pytest** | `tests/test_health.py` 绿 |
| **verify** | PASS |
| **下一棒** | 维护者配 Secrets → `workflow_dispatch` |
