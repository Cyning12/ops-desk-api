# Task：fix · deploy-api SSH 长构建断连（ServerAlive keepalive）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：fix / CI 部署稳定性  
> **现象**：deploy-api 两次失败（run 32816733168 初跑+重跑）：远端 docker build 下载 torch（526MB，~4.5min）期间 SSH `client_loop: send disconnect: Broken pipe` exit 255  
> **根因**：buildkit 大包下载期间无输出流经 SSH 通道，中间链路/NAT 断开空闲连接  
> **修法**：`.github/workflows/deploy-api.yml` SSH_OPTS 增 `-o ServerAliveInterval=30 -o ServerAliveCountMax=10 -o TCPKeepAlive=yes`  
> **分支**：`fix/deploy-ssh-keepalive`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `fix-deploy-ssh-keepalive` |
| **git_branch** | `fix/deploy-ssh-keepalive` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | yaml 语法校验；合并后 rerun deploy-api 实证（真验收） |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者报 CI 失败指示处理 + 本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（单行 CI 配置修复，根因已复现确认） |

---

## 验收标准

- [x] SSH_OPTS 增 keepalive 三项（yaml 语法有效 · python yaml.safe_load 通过；rsync `-e ssh` 同步补齐）
- [ ] 合并后 `gh run rerun` deploy-api 通过（或失败点不再是 SSH 断连）
- [x] graph-compile exit 0（无关联但过闸）

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：SSH keepalive 修 deploy 断连 |
| 2026-08-25 | 30 执行：SSH_OPTS 与 rsync `-e ssh` 均加 `ServerAliveInterval=30 ServerAliveCountMax=10 TCPKeepAlive=yes`；yaml 校验过；graph-compile exit 0；diff 仅限 deploy-api.yml（未 commit，待 00 统一提交） |
| 2026-08-25 | keepalive 合并后实证：run 32818362999 连接 30 分钟无 Broken pipe（修复生效），但被 job 自有 `timeout-minutes: 30` 取消——暴露第二约束（PR #45 改 requirements 致依赖缓存层失效，torch 等全量重装超 30min）。修法：timeout 30→60（fix/deploy-job-timeout） |
