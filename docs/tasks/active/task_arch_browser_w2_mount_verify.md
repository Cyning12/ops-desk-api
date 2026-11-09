# Task：arch-browser W2 API 挂载与 dist 完整性验证

> **状态**：in_progress  
> **类型**：验证/部署准备  
> **关联图谱**：无  
> **落盘**：`docs/tasks/active/task_arch_browser_w2_mount_verify.md`；验收后 `git mv` → `docs/tasks/done/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `arch-browser-w2-mount-verify` |
| **test_strategy** | `required` |
| **test_strategy_note** | 启动本地 uvicorn 后断言 `/docs/arch-browser/` 与样例 MD 路径返回 200；断言 dist 静态文件已入库 |
| **code_quality_bar** | `recommended` |
| **orchestration** | 单 task |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/arch-browser-w2-mount-verify` |
| **graph_delta** | `none` |
| **graph_delta_note** | 不新增模块/路由/表；只验证既有 FastAPI mount 与 dist 产物 |
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

W2 目标：让 arch-browser 可通过生产域名公开访问。本任务聚焦 ops-desk-api 侧：`app/main.py` 已把 `docs/arch-browser/dist` mount 到 `/docs/arch-browser`，且 W1 已实现白名单 MD 复制进 dist。本任务验证该 mount 在本地/CI 能正常服务，并确保 dist 产物随仓入库。

**完成态**：

- [ ] 本地启动 api 后，`GET /docs/arch-browser/` 返回 200 与 `index.html`。
- [ ] 样例 MD 路径（如 `/docs/arch-browser/docs/_tech_graph/l1/01_modules.md`）返回 200。
- [ ] 白名单外的 dist 路径按 StaticFiles 行为返回 404。
- [ ] `dist/` 关键文件（`index.html`、`site-data.json`、白名单 MD）已提交入库。
- [ ] 自检结论回填。

**不做**：

- 修改 Nginx 配置（由 workspace 子任务负责）。
- 新增 FastAPI 路由或业务代码。
- 变更 W1 白名单。

---

## 范围

- [ ] `app/main.py` 现有 mount 的验证（必要时补全路径/参数）
- [ ] `docs/arch-browser/dist/` 产物确认与提交
- [ ] （可选）测试脚本或 CI 步骤，确保 build 后的 dist 不被遗漏

## 非范围

- `ops-desk-workspace/deploy/nginx/ops-desk.conf`
- 前端 Vue 登录守卫
- TLS/SSL 证书

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `docs/arch-browser/dist/index.html` 缺失 | mount 注册失败或返回 404 | 运行 build_site.py | 404 |
| 样例 MD 未复制进 dist | 返回 404 | 检查白名单与 build | 404 |
| uvicorn 启动失败 | 无法验证 | 检查依赖/env | 错误日志 |

---

## 验收标准

- [ ] `python3 docs/arch-browser/scripts/build_site.py` 退出码 0。
- [ ] `uvicorn app.main:app --port 8000` 启动后：
  - [ ] `GET /docs/arch-browser/` → 200
  - [ ] `GET /docs/arch-browser/docs/_tech_graph/l1/01_modules.md` → 200
  - [ ] `GET /docs/arch-browser/docs/discussions/agent-host-current-architecture/modules/M01_capability-registry.md` → 200
  - [ ] `GET /docs/arch-browser/docs/not_in_whitelist.md` → 404（若文件不存在）
- [ ] `git status` 中 `docs/arch-browser/dist/` 无未提交的必备文件缺失。
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_arch_browser_w2_mount_verify.md` 通过。
- [ ] 提交到 `task/arch-browser-w2-mount-verify` 并创建 PR。

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/spec/arch-browser/01_execution_waves.md`
3. `app/main.py`
4. `docs/arch-browser/scripts/build_site.py`
5. `docs/arch-browser/dist/`

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| mount 验证 | ⏳ | |
| dist 入库检查 | ⏳ | |
| CI/测试脚本 | ⏳ | 可选 |

---

## 测试策略（Harness）

**test_strategy**: `required`

- 本地启动 uvicorn，用 curl/HTTP 客户端访问 mount 路径。
- 验证直接访问静态文件与目录根目录。

---

### 自检结论（执行者）

（30/40 回填）

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
