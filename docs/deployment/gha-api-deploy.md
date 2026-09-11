# GitHub Actions · 后端自动部署（合入 master）

> **日期**：2026-07-28  
> **Workflow**：`.github/workflows/deploy-api.yml`  
> **SPEC**：`docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md`  
> **范围**：rsync `/opt/ops-desk/api` + 远端 `docker compose … up -d --build api`；**不**部署 web dist、**不** reload Nginx、**不**重建 db  
> **手动应急**：`ops-desk-workspace/deploy/deploy.sh --skip-web`  
> **生产验收**：2026-07-28 通过（run `30327570930` · health `{"status":"ok"}`）

---

## 触发

| 事件 | 行为 |
|---|---|
| `push` → `master`（含 PR merge） | 同步源码并重建 api 容器 |
| `workflow_dispatch` | Actions 页手动重跑部署 |

校验仍由 `.github/workflows/pytest.yml` / `tech-graph.yml` 负责；本 workflow 为 **发版通道**。

---

## 所需 GitHub Secrets

在仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 示例 / 说明 |
|---|---|
| `DEPLOY_HOST` | 服务器公网 IP 或域名（可与 web 同机） |
| `DEPLOY_USER` | SSH 用户（现网常用 `ubuntu`） |
| `DEPLOY_SSH_KEY` | **无口令** ed25519 私钥全文；可 **复用** web 已配 key |
| `DEPLOY_API_PATH`（可选） | 默认 `/opt/ops-desk/api`（**禁止**指向 `/opt/ops-desk/web/**`） |
| `DEPLOY_COMPOSE_DIR`（可选） | 默认 `/opt/ops-desk/deploy` |

本机带 passphrase 的 lighthouse 私钥 **不能**直接给 Actions。

---

## 一次性：服务器权限（相对 web 的增量）

web 只写用户目录下 `dist/`；api 需要 `docker compose`。择一并写死：

1. **推荐**：`DEPLOY_USER` 加入 `docker` 组，workflow 内 **无 sudo**  
2. `/etc/sudoers.d/` 对 compose 相关命令 NOPASSWD，并把 workflow 中的 `docker` 改为 `sudo docker`  
3. 服务器封装脚本，GHA 只调该脚本（需改 workflow）

**目录属主（C3）**：一次性保证 api 目录对 `DEPLOY_USER` 可写（workflow **默认不**每次 chown）：

```bash
ssh ops-desk 'sudo chown -R ubuntu:ubuntu /opt/ops-desk/api'
```

（若此前 `deploy.sh` 已做过可跳过。）

**compose 文件**：须已存在于服务器 `$DEPLOY_COMPOSE_DIR/docker-compose.prod.yml`（首次用手动 `deploy.sh` 同步）。本 workflow **不**从 `ops-desk-workspace` 拉 compose。

---

## 一次性：密钥与 Secrets（可复用 web）

若 web 已配 `ops-desk-gha-deploy`，api 仓可直接：

```bash
cd /path/to/ops-desk-api
gh secret set DEPLOY_HOST --body "YOUR_SERVER_IP"
gh secret set DEPLOY_USER --body "ubuntu"
gh secret set DEPLOY_SSH_KEY < ~/.ssh/ops-desk-gha-deploy
# 可选：
# gh secret set DEPLOY_API_PATH --body "/opt/ops-desk/api"
# gh secret set DEPLOY_COMPOSE_DIR --body "/opt/ops-desk/deploy"
```

新建专用 key 时：

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/ops-desk-api-gha-deploy -C "ops-desk-api-gha-deploy"
ssh-copy-id -i ~/.ssh/ops-desk-api-gha-deploy.pub ops-desk
```

验证：

```bash
ssh -i ~/.ssh/ops-desk-gha-deploy -o BatchMode=yes ubuntu@YOUR_SERVER_IP \
  'docker compose version && curl -fsS http://127.0.0.1:8000/health'
```

---

## 验收

1. Secrets + docker 权限 + api 目录可写就绪  
2. GitHub → Actions → **deploy-api** → **Run workflow**  
3. Job 绿；远端 `curl -fsS http://127.0.0.1:8000/health` → `{"status":"ok"}`（无 `probe`）  
4. 确认 **未**改动 `/opt/ops-desk/web/dist`；**未** reload Nginx  

若报「缺少 Secret …」：对照上表补齐后重跑。

---

## 与手动部署的关系

| 方式 | 命令 / 入口 | 说明 |
|---|---|---|
| GHA（推荐日常） | merge `master` 或 `workflow_dispatch` | 仅 api；`up -d --build api` |
| 手动仅后端 | `deploy.sh --skip-web` | 另含 Nginx reload |
| 手动改 Nginx | `deploy.sh --nginx-only` | 本 GHA **不**做 |
| 手动全量 | `deploy.sh` | web+api+nginx |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 初版（task `gha-deploy-api` · C1–C3） |
