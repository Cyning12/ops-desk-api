# Task：生产部署 v1（API + PG + Web + Nginx + SSL）

> **状态**：in_progress  
> **类型**：部署运维（Epic 8 核心）  
> **关联**：`ops-desk-workspace/docs/04-infrastructure/deploy-info.local.md` · `docker-compose.yml` · `ops-desk-web/docs/deployment/nginx-static-hosting.md`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `deploy-prod` |
| **test_strategy** | `required` |
| **test_strategy_note** | WS 开关单测；部署后 E2E checklist（HTTPS 登录/overview/issues/pulls/graph/chat）人工验收 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task（跨仓：ops-desk-api 代码 + ops-desk-workspace 部署产物 + 服务器执行） |
| **git_branch** | `task/deploy-prod`（api）· workspace 改动随行提交 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 用户确认：chat 模块加 WS 开关；部署产物不入 graph |
| **HG-AUDIT-R1** | approved | **30** | 用户确认：范围含真实服务器操作；SSL 证书执行时由用户提供 |

---

## 背景与目标

Epic 3–6 后端、Web 前端 v1 全部完成；域名 `www.cynaya.cn` 已备案并解析到服务器 `82.157.125.39`（SSH 免密已通，Docker 29.6.1 / Nginx 1.18.0 已装）。执行首次生产部署。

**已拍板决策**：

| 项 | 决策 |
|---|---|
| 范围 | API + PG + Web（单域名路径分流：`/` → web 静态，`/api` → API） |
| WS 端点 | 新增 `OPS_CHAT_WS_ENABLED` 开关，生产置 `false`（未鉴权，公网禁用） |
| SSL | 腾讯云控制台下载 Nginx 格式证书，部署时 scp 上服务器 |
| Web 构建 | 本地 `pnpm build` → rsync `dist/` 上服务器（服务器不装 node） |
| 数据 | 服务器上跑 `import_from_supabase.py`（`SUPABASE_DATABASE_URL` 仅存在于服务器 `.env`） |
| 部署目录 | `/opt/ops-desk` |
| CI/CD | v1 手动部署脚本；GHA 推送留后续 |

**完成态**：

- [ ] `OPS_CHAT_WS_ENABLED` 开关（默认 true，false 时 WS 路由 404）+ 单测
- [ ] 生产 compose（`ops-desk-workspace/deploy/docker-compose.prod.yml`：db + api）
- [ ] Nginx 配置模板（TLS、`/` 静态、`/api` 反代、SSE `proxy_buffering off`、gzip）
- [ ] 部署脚本 `ops-desk-workspace/deploy/deploy.sh`（build web → rsync → 服务器 build/up/migrate）
- [ ] 服务器 `/opt/ops-desk/.env` 生产值（SECRET 生成、DB 密码、LLM keys、cookie secure、CORS、WS 禁用）
- [ ] SSL 证书部署（用户提供 crt/key → scp）
- [ ] 数据库初始化：migrate + 初始 maintainer + Supabase 数据导入
- [ ] E2E checklist 全过（HTTPS）
- [ ] invoke 落盘 + `harness task close` 归档

**不做**：

- GHA CI 推送部署、域名裸域跳转 www、CDN、备份策略（Epic 8.6 后续）、多实例

---

## 范围

- [ ] `app/ops/router.py` / `app/ops/chat/ws.py`（WS 开关）
- [ ] `app/config.py`（`ops_chat_ws_enabled`）
- [ ] `tests/test_chat_ws.py`（开关单测）
- [ ] `ops-desk-workspace/deploy/`（compose.prod、nginx 模板、deploy.sh、README）
- [ ] `ops-desk-workspace/docs/04-infrastructure/deploy-info.local.md`（执行回填）

## 非范围

- Web/iOS 代码改动
- CI Secrets 配置（v1 手动）

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| SSH 不通 | deploy.sh 退出非零 + 检查提示 | 是 | 部署中止 |
| 证书缺失/路径错 | Nginx `configtest` 失败，不 reload | 是 | 站点不可达（部署中止） |
| api 容器健康检查失败 | compose 输出日志，deploy.sh 退出非零 | 是 | 部署中止 |
| 数据导入失败 | 不影响站点可用性；按导入指引重跑 | 是 | 列表空态 |
| 迁移失败 | alembic 报错，deploy.sh 中止 | 是 | 部署中止 |

---

## 验收标准

- [ ] `pytest tests` 通过（含 WS 开关单测）
- [ ] `ruff check app tests` 通过
- [ ] 生产 `OPS_CHAT_WS_ENABLED=false` 时 `wss://www.cynaya.cn/api/ops/chat/ws` 不可达
- [ ] `https://www.cynaya.cn/` 打开 Web 登录页（HTTP 自动跳 HTTPS）
- [ ] 邀请密钥登录 → Overview/Issues/PRs/Graph 显示真实数据
- [ ] Chat 页面 SSE 流式回答可用（经 Nginx 反代无缓冲）
- [ ] 服务器重启后 `docker compose` 服务自启（restart policy）

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `ops-desk-workspace/docs/04-infrastructure/deploy-info.local.md`（真值）
3. `ops-desk-workspace/docs/04-infrastructure/01-environment-setup.md`（SSL/Nginx 章节）
4. `ops-desk-web/docs/deployment/nginx-static-hosting.md`
5. `docker-compose.yml` · `Dockerfile`
6. `app/ops/chat/ws.py`

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| WS 开关 | ⏳ | `OPS_CHAT_WS_ENABLED`，默认 true |
| 生产 compose | ⏳ | workspace/deploy/ |
| Nginx 模板 | ⏳ | TLS + 路径分流 + SSE |
| deploy.sh | ⏳ | build→rsync→up→migrate→import |
| E2E | ⏳ | HTTPS checklist |

---

### 自检结论（执行者）

（30/40 回填）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-25 | 创建 task，匹配分支 `task/deploy-prod`；deploy-info §1–§3 已就绪 |
