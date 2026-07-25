# Invoke：30 执行编码 · prod-e2e-handoff

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环）+ CLOSE |
| task_slug | `prod-e2e-handoff` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_prod_e2e_handoff.md` |
| related_review_or_none | `docs/harness/reviews/task_prod_e2e_handoff_audit_R1_20260725.md` |
| git_branch | `fix/prod-e2e-handoff` |
| worktree_root | — |
| created_utc_or_local | 2026-07-25 |
| notes | 生产联调终报移交；kimi 完成改码/部署验证；接手方补 invoke + close |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_prod_e2e_handoff.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：fix/prod-e2e-handoff
- F2：Settings 空串 OPS_LLM_MODEL 回退 catalog 默认 + 单测
- workspace：compose 移除 OPS_LLM_MODEL=；nginx index.html no-cache
- F1：仅核查（module_matrix 源数据真空），不改码
- test_strategy: required

【Verify】
- pytest tests · 生产 Chat done.model 非空 · index.html Cache-Control: no-cache
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（87 passed）· `ruff check app tests`（绿）· 生产 curl：`done.model=deepseek-ai/DeepSeek-V4-Pro`；`index.html` → `Cache-Control: no-cache`
- **变更路径**：
  - api：`app/config.py`、`tests/test_config.py`、`docs/tasks/active/task_prod_e2e_handoff.md`
  - workspace（已 commit）：`deploy/docker-compose.prod.yml`、`deploy/nginx/ops-desk.conf`
- **生产动作**：`deploy.sh --skip-web` 重载 nginx + api；Chat SSE / index 头已复核
- **下一棒**：CLOSE → PR（api `fix/prod-e2e-handoff`）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-25 | 30/40 完成；接手补 invoke 落盘 |
