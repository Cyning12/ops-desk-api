# SPEC：ops-desk-api GitHub Actions 自动部署（对齐 web）+ 移除临时 health probe（v1）

> **状态**：`draft`（待 HG-SPEC-SIGNOFF）  
> **track**：`feature`（基础设施 / CI·CD）  
> **上游**：维护者 2026-07-28 · health 探针验收完成 · 「参照 web 自动构建，顺便删除 probe」  
> **金样**：`ops-desk-web` · `.github/workflows/deploy-web.yml` · `docs/deployment/gha-frontend-deploy.md` · task `web-gha-deploy-frontend`  
> **关联现状**：生产仍靠 `ops-desk-workspace/deploy/deploy.sh --skip-web`；`/health` 临时含 `probe=20260728-a`（PR #16）  
> **下游**：人签 SPEC → 00 起草 task → 20-task-audit → 30 实现  
> **Open Folder（实现）**：`ops-desk-api/`（workflow / 文档 / 去 probe）；服务器 Secrets 与 sudo/docker 属维护者一次性操作

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **spec_slug** | `gha-deploy-api` |
| **invoke_slug** | `gha-deploy-api`（task 阶段） |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 去 probe：`pytest tests/test_health.py`；deploy workflow：缺 Secrets 时失败信息可读；**不**在 CI 内真实 SSH 打生产（验收靠 `workflow_dispatch` + 维护者确认） |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `master`（对齐本仓；对照 web 的 `main`） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | pending | 人签本 SPEC 后方可 00 出 task |

---

## 1. 背景与目标

### 现状

| 层 | 现状 |
|---|---|
| 前端 | 合入 `main` → GHA `deploy-web`：`pnpm build` + rsync `dist/`；Secrets 已通 |
| 后端 | 合入 `master` **无**自动发版；维护者本机 `./deploy.sh --skip-web` → rsync api + 服务器 `docker compose up -d --build` |
| 探针 | `/health` 含临时 `probe`；验收已完成，须删除 |

### 一句话目标

在 **ops-desk-api** 增加与 web **同形态**的 GHA 部署通道：push/`workflow_dispatch` → 同步后端源码到服务器 → 远程重建并重启 api 容器；**同波**去掉临时 `probe`；保留 `deploy.sh --skip-web` 作应急。

---

## 2. 范围

### D1 · 去掉临时探针（同波必做）

- `app/main.py`：`GET /health` 恢复为仅 `{"status":"ok"}`（删 `probe` 字段与注释）
- `tests/test_health.py`：断言同步恢复
- 关闭 / 归档 `task_health_temp_probe`（`harness task close` 或随实现 PR 迁 `done/`）

### D2 · GHA workflow（对齐 web 形态）

新增 `.github/workflows/deploy-api.yml`（名称可微调，须在文档与本 SPEC 一致）：

| 项 | 约定 |
|---|---|
| 触发 | `push` → `master`；`workflow_dispatch` |
| Runner | `ubuntu-latest`；合理 timeout（建议 ≥20min，含镜像 build） |
| Checkout | 本仓 `ops-desk-api` |
| 同步 | rsync 后端源码 → 服务器 `/opt/ops-desk/api/`（排除 `.venv` / `__pycache__` / `.git` / `.env` / `node_modules` / `.pytest_cache`，对齐 `deploy.sh`） |
| 重建 | SSH 远端执行等价于：`cd /opt/ops-desk/deploy && sudo docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env up -d --build`（**仅重建/重启 api 相关**；不得部署 web `dist/`） |
| 健康检查 | 远端 `curl -fsS http://127.0.0.1:8000/health` 轮询至成功或超时失败（对齐 `deploy.sh`） |
| Secrets 门闩 | 缺 `DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_SSH_KEY` 时 **显式失败**并指向文档（照抄 web `Require deploy secrets` 风格） |

**不**在 GHA 内：`pnpm`/`pytest` 全量（仍由现有 `pytest.yml` / `tech-graph.yml` 负责校验）；本 workflow 是 **发版通道**。

### D3 · 文档

- 新增 `docs/deployment/gha-api-deploy.md`（对照 web `gha-frontend-deploy.md`）：触发、Secrets、一次性 deploy key / sudo·docker 权限、验收步骤、与 `deploy.sh` 关系
- `README.md` 或部署相关入口加一句指针（若仓内已有部署小节则挂链；无则最小增量）

### D4 · Secrets 与服务器一次性（维护者；Agent 不写私钥入仓）

| Secret | 说明 |
|---|---|
| `DEPLOY_HOST` | 与 web 同机即可 |
| `DEPLOY_USER` | 与 web 同（现网常用 `ubuntu`） |
| `DEPLOY_SSH_KEY` | **无口令** ed25519 私钥全文；可 **复用** web 已配 key，或另建 `ops-desk-api-gha-deploy` |
| `DEPLOY_API_PATH`（可选） | 默认 `/opt/ops-desk/api` |
| `DEPLOY_COMPOSE_DIR`（可选） | 默认 `/opt/ops-desk/deploy` |

**权限缺口（相对 web）**：web 只写用户目录下 `dist/`；api 需 `docker compose`（现网 `deploy.sh` 用 `sudo`）。实现前维护者须择一并在文档写死：

1. **推荐**：部署用户加入 `docker` 组，远端命令 **无 sudo**；或  
2. `/etc/sudoers.d/` 对 compose 相关命令 NOPASSWD；或  
3. 服务器已有封装脚本，GHA 只调该脚本  

未解决则 `workflow_dispatch` 验收会红——属 **failure_path**，非代码 bug。

**compose 文件来源**：默认 **不**每次从本仓同步 `ops-desk-workspace/deploy/`（避免跨仓 checkout）。假定服务器已有可用的 `docker-compose.prod.yml`；compose 变更仍走 workspace + 手动/`deploy.sh`。若首次发现远端缺文件 → 失败可读 + 文档指引。

---

## 3. 非范围

- 改业务 `app/ops/**` 行为（除去掉 probe）
- 自动部署前端 / 改 `deploy-web.yml`
- 把 `ops-desk-workspace/deploy/**` 搬进 api 仓或改默认分支名
- 正式 `git_sha` / `version` 暴露接口（可另开 SPEC；本波仅删临时 probe）
- 灰度、多实例、零停机（v1 单实例短暂停机可接受，与既有 `deploy.sh` 一致）
- Agent 向 GitHub / 服务器写入真实私钥或生产 `.env`
- Epic 8.6 备份策略、强制 pre-commit

---

## 4. 验收清单

### 去探针

- [ ] `GET /health`（服务器本机 `:8000`）仅为 `{"status":"ok"}`，无 `probe`
- [ ] `pytest tests/test_health.py` 绿

### GHA 部署

- [ ] 仓库存在 `deploy-api`（或约定名）workflow；触发含 `master` push + `workflow_dispatch`
- [ ] Secrets 未配时 job 失败信息指出缺项与文档路径
- [ ] Secrets 与远端权限就绪后：`workflow_dispatch` 绿
- [ ] 远端 `/opt/ops-desk/api` 内容更新；api 容器重建；`:8000/health` 返回 ok
- [ ] **未**改动 `/opt/ops-desk/web/dist`（对照 web 边界）
- [ ] 文档 `docs/deployment/gha-api-deploy.md` 可独立照做
- [ ] 应急路径仍成立：`deploy.sh --skip-web`

---

## 5. 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| Secrets 缺失 | job 显式失败 + 文档指针 | 是（配齐后 re-run） |
| SSH 拒连 / 安全组 | job 红；查 key / authorized_keys | 是 |
| 无 docker/sudo 权限 | job 红；按文档补 docker 组或 sudoers | 是（人） |
| compose 目录缺失 | job 红；指引先跑一次手动 deploy | 是（人） |
| 镜像 build / health 超时 | job 红；查 `docker compose logs api` | 是 |
| 与 web 并发部署 | 可并行（不同路径）；勿互相 `--delete` 错目录 | 是 |

---

## 6. 方案对比（R2）

| 方案 | 做法 | 优劣 | 结论 |
|---|---|---|---|
| **A. GHA rsync api + SSH compose --build** | 对齐 `deploy.sh --skip-web` 实质；金样贴近 web（SSH+rsync） | 需解决远端 docker 权限；构建在服务器耗时 | **推荐** |
| B. GHA 只 rsync，不 --build | 快，但 Python/依赖变更不进容器 | 易「以为发了其实旧镜像」 | 弃 |
| C. GHA build 镜像 push 到仓库再 pull | 标准 CD | 引入 Registry、凭证、改 compose；超本波 | 弃（可后续 SPEC） |
| D. 仅文档要求继续手动 deploy.sh | 零开发 | 不满足「参照 web 自动构建」 | 弃 |

---

## 7. 思考轮

### R0 · 问题框定

验收完临时 probe 后，后端仍无合入自动发版；web 已具备 GHA 金样。需求合并为：自动部署 + 删除探针。

### R1 · 范围 / 非范围 / 角色

- **角色**：维护者（Secrets/权限）· 30 Agent（workflow+文档+去 probe）· 运行时服务器单实例  
- **场景**：merge `master` 日常发版；Actions 手动 `workflow_dispatch` 验收；应急仍本机 `deploy.sh`

### R2 · 方案对比

见 §6；推荐 **A**。

### R3 · 边界 / 失败 / 安全

- 私钥仅 Secrets；无口令 key；可与 web 复用同机同 key  
- 生产 `.env` 留服务器，GHA **不**下发密钥内容到日志  
- sudo/docker 为相对 web 的增量风险，必须文档化  
- 短暂停机可接受；不做灰度  
- 不误伤 web dist

### R4 · 验收 / 可测性

- 去 probe：单测必测  
- deploy：机械上 Secrets 门闩可测（脚本层）；真连生产靠维护者 dispatch，标 `recommended` 而非强制 CI 内 SSH

### R5 · 签收就绪

SPEC 可交人签 `HG-SPEC-SIGNOFF`；签收后 00 出 task（建议 slug：`gha-deploy-api`；可含子清单「先去 probe 或同 PR」）。

---

## 8. 思考轮控制表

| 字段 | 值 |
| --- | --- |
| `actual_last_round` | R5 |
| `early_stop` | no |
| `early_stop_reason` | — |
| `residual_risks` | ① 远端 docker/sudo 未配齐则首轮 dispatch 必红；② 复用 web key 的权限面扩大到可触发 compose——须接受或拆 key；③ 服务器 compose 与 workspace 漂移时 GHA 不同步 deploy/ 目录；④ 构建耗时可能导致 timeout，需按实测调高 |

---

## 9. 下一棒 Prompt（人签 SPEC 后）

### 9.1 · 20-spec-audit（可选轻量）或人直接签收

`````text
你是 Harness 20-spec-audit。Open Folder = ops-desk-api 仓根。

读：
- docs/spec/SPEC-gha-deploy-api_v1.md
- docs/harness/prompts/20-spec-audit.md
- 金样：../ops-desk-web/.github/workflows/deploy-web.yml
- 金样文档：../ops-desk-web/docs/deployment/gha-frontend-deploy.md

输出书面审查（pass|conditional_pass|fail）；建议 HG-SPEC-SIGNOFF（不代签）。
重点核对：范围/非范围、与 web 边界、docker/sudo 失败路径、去 probe 同波、不误伤 web dist。
`````

### 9.2 · 人签后 · 00 起草 task（可复制）

`````text
你是 Harness 00。Open Folder = ops-desk-api。

依据已签收 docs/spec/SPEC-gha-deploy-api_v1.md 起草 task：
- slug: gha-deploy-api
- 分支: task/gha-deploy-api（自 origin/master）
- 范围：去 /health probe + deploy-api.yml + docs/deployment/gha-api-deploy.md
- graph_change_layer: none；invoke_retention_profile: minimal；对照 web-gha-deploy-frontend
- 人工闸表预置；勿改 app/ops 业务逻辑
`````

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 10-spec 初稿：对齐 web GHA + 同波删 probe |
