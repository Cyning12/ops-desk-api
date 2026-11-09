# Task：arch-browser W2 Nginx 生产入口代理配置

> **状态**：in_progress  
> **类型**：部署配置  
> **关联图谱**：无  
> **落盘**：`../ops-desk-workspace/docs/tasks/active/task_arch_browser_w2_nginx_proxy.md`；验收后 `git mv` → `docs/tasks/done/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `arch-browser-w2-mount-verify` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 在本地用 nginx -t 校验配置文件语法；用 curl 通过 nginx 访问 /docs/arch-browser/ 路径 |
| **code_quality_bar** | `recommended` |
| **orchestration** | 单 task |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/arch-browser-w2-nginx-proxy` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅修改 Nginx 配置，不新增模块/路由/表 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **wiki_promotion** | `none` |
| **close_pr_policy** | `required` |
| **experience_capture** | `recommended` |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者授权直接开工 |
| **HG-AUDIT-R1** | approved | 30 | 维护者口头授权 W2 开工（m00153） |
| **HG-GRAPH-MODULES** | approved | 30 | 不修改图谱 |

---

## 背景与目标

W2 目标：让 arch-browser 可通过 `https://www.cynaya.cn/docs/arch-browser/` 公开访问。ops-desk-api 侧已把 `docs/arch-browser/dist` mount 到 `/docs/arch-browser`；本任务在 workspace 的 Nginx 配置里增加对应 location，使公网流量通过 Nginx → api 获取静态内容。

**完成态**：

- [ ] `deploy/nginx/ops-desk.conf` 新增 `location /docs/arch-browser/`。
- [ ] 配置支持 trailing slash 与目录根访问（返回 `index.html`）。
- [ ] `nginx -t` 语法校验通过。
- [ ] `deploy/README.md` 更新相关部署说明。
- [ ] 自检结论回填。

**不做**：

- 修改 ops-desk-api 代码或 dist 内容。
- 处理 TLS 证书（已有配置）。
- 修改前端 Vue 登录守卫。

---

## 范围

- [ ] `deploy/nginx/ops-desk.conf`
- [ ] `deploy/README.md`（部署说明更新）

## 非范围

- `ops-desk-api/app/main.py`
- `ops-desk-api/docs/arch-browser/dist/`
- SSL 证书路径与生成

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| nginx 配置语法错误 | `nginx -t` 失败，禁止 reload | 修正后重试 | 部署失败 |
| api 未启动或 mount 异常 | 返回 502/404 | 检查 api 侧 W2 mount verify task | 502/404 |
| trailing slash 不匹配 | 资源路径 404 | 调整 location/rewrite | 404 |

---

## 验收标准

- [ ] `deploy/nginx/ops-desk.conf` 新增 `location /docs/arch-browser/`。
- [ ] 配置至少覆盖：
  - [ ] `proxy_pass http://127.0.0.1:8000/docs/arch-browser/;`
  - [ ] 透传必要 header（Host、X-Real-IP、X-Forwarded-For、X-Forwarded-Proto）
  - [ ] 或改为 alias 磁盘 dist 目录并验证缓存策略
- [ ] `nginx -t` 在本地/容器内通过（可 dry-run 或 staging 容器）。
- [ ] `deploy/README.md` 有 arch-browser 公开入口的部署说明。
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_arch_browser_w2_nginx_proxy.md` 通过（如 workspace 已接入 spec-wave）。
- [ ] 提交到 `task/arch-browser-w2-nginx-proxy` 并创建 PR。

---

## 给执行帽的必读列表

1. `../ops-desk-workspace/AGENTS.md`（如存在）
2. `deploy/nginx/ops-desk.conf`
3. `deploy/README.md`
4. `ops-desk-api/docs/spec/arch-browser/01_execution_waves.md`
5. `ops-desk-api/app/main.py`

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| location 配置 | ⏳ | 推荐 proxy_pass 到 api，便于统一版本 |
| header 透传 | ⏳ | |
| README 更新 | ⏳ | |
| nginx -t 校验 | ⏳ | |

---

## 测试策略（Harness）

**test_strategy**: `recommended`

- 本地/容器运行 `nginx -t` 校验。
- 如条件允许，启动 nginx + api，curl `/docs/arch-browser/` 与样例 MD 路径。

---

### 自检结论（执行者）

- `python3 docs/arch-browser/scripts/build_site.py` → exit 0
- `uvicorn app.main:app --port 8000` 启动后：
  - `GET /docs/arch-browser/` → 200
  - `GET /docs/arch-browser/docs/_tech_graph/l1/01_modules.md` → 200
  - `GET /docs/arch-browser/docs/discussions/agent-host-current-architecture/modules/M01_capability-registry.md` → 200
  - `GET /docs/arch-browser/docs/not_in_whitelist.md` → 404
- `npx spec-wave task lint` → PASS
- `ruff check app tests` → All checks passed!
- `npx spec-wave verify` → VERIFY: PASS

---

### KPI（00）

（关账回溯填写）

---

### 经验总结

（关账必填）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-11-09 | 创建 task，维护者授权 W2 开工（m00153） |
