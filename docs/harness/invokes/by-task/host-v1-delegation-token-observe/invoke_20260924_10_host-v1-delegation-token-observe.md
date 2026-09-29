# Invoke · 10-task 起稿 · host-v1-delegation-token-observe（D2 第一闸 · 本地观察准备）

> **日期**：2026-09-24 · **帽**：10-task（00 亲起 · SPEC §2 D2 已 sanction 第一闸 task 化准备）  
> **维护者令（原话留痕）**：「仓内改动也可以吧，LG_RAG_DELEGATION_TOKEN_SECRET本地如何生成？落盘一份完成的本地checklist」（2026-09-24 · D2 推进窗口）· 承「签收，生成00 Prompt，在新窗口开始D1统筹」（2026-09-24）与 2026-09-23 长程令  
> **SPEC 真值**：`docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md`（signed · §2 D2 六闸矩阵第一闸 + 报告格式钉死）  
> **产出**：`docs/tasks/active/task_host_v1_delegation_token_observe.md`（CLOSE 后归档：`docs/tasks/done/task_host_v1_delegation_token_observe.md`）

## 起稿要点

| 项 | 值 |
|---|---|
| 类型 | config+docs（compose env 透传 + RUNBOOK + env 样例 + 报告模板 · 零 `app/` 码改 · `graph_change_layer=none`） |
| 范围 | 四件钉死：RUNBOOK 本地 checklist（主交付）· compose 三键（默认 `off`/空/600）· `.env.example` 注释键 · `reports/gate_observe/_TEMPLATE_delegation_token.yaml` |
| 非范围 | 开闸执行与首份报告（下一棒 · 维护者本地跑）· 其余五闸 · enforce · Langfuse 本地引入 |
| 闸表 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved（**00 代录** · 配置面+docs 承 task_agent_host_framework_alignment 先例） |
| 铁律 | 默认关（不设 env = off 零 diff）· 密钥禁入库（只写生成命令）· 记动作不记内容 · 宁停勿闯 |
| invoke 留档 | `required_invoke_hats=10,40`（40 于 CLOSE 落盘） |

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 10 立稿（00 亲起 · 三闸代录 approved · 维护者令原话留痕） |
