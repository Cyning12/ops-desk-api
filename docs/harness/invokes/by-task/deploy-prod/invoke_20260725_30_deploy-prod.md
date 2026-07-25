# Invoke：30 执行编码 · deploy-prod

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `deploy-prod` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_deploy_prod.md` |
| related_review_or_none | `docs/harness/reviews/task_deploy_prod_audit_R1_20260725.md` |
| git_branch | `task/deploy-prod` |
| worktree_root | — |
| created_utc_or_local | 2026-07-25 |
| notes | 用户批准含真实服务器操作；SSL 证书执行时由用户提供 |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_deploy_prod.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@ops-desk-workspace/docs/04-infrastructure/deploy-info.local.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表，比对用户声称）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：task/deploy-prod（api）· workspace deploy/ 产物随行
- 范围：OPS_CHAT_WS_ENABLED 开关 + 单测、生产 compose、Nginx 模板、
  deploy.sh、服务器 .env、SSL 部署、数据初始化、HTTPS E2E
- test_strategy: required

【Verify】
- pytest tests · ruff check app tests · HTTPS E2E checklist
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（86 passed）· `ruff check app tests`（绿）· HTTPS E2E 全过（登录/Overview/issues 599/pulls 1440/graph/Chat SSE/WS 拒 404）
- **变更路径**：
  - api：`app/config.py`、`app/ops/chat/ws.py`、`tests/test_chat_ws.py`、`Dockerfile`（国内镜像 + PYTHONPATH）
  - workspace：`deploy/{docker-compose.prod.yml,nginx/ops-desk.conf,deploy.sh,.env.example,README.md}`、`docs/04-infrastructure/deploy-info.local.md`（gitignored 回填）
- **服务器变更**：`/opt/ops-desk/`（api 源码、deploy、web/dist、.env chmod 600）、`/etc/nginx/ssl/cynaya.cn.{crt,key}`、sites-enabled/ops-desk、docker daemon.json 镜像加速、Lighthouse 防火墙 443（用户控制台）
- **生产数据**：Supabase 导入 2/49/599/1440/47/44；maintainer admin 已建（invite token 已交付用户）
- **过程修复**：Docker Hub 超时 → mirror.ccs.tencentyun.com；apt/pip 国内镜像；PYTHONPATH=/app；443 防火墙
- **下一棒**：CLOSE → PR；后续 Epic 8.6 备份策略、GHA CI 推送

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-25 | 30 执行 + 40 自检完成落盘 |
