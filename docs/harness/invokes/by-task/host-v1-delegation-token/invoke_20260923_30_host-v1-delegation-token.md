# Invoke · 30（改码 · 委派子 Agent）· host-v1-delegation-token

> **日期**：2026-09-23  
> **帽**：30（**00 委派子 Agent 执行** · 承 harness-00-delegate-only · 00 不亲自 30）  
> **闸态（下发时真值 · task 人工闸表）**：HG-TASK-DRAFT=approved · HG-AUDIT-R1=**approved**（2026-09-23 · 00 代录 · 维护者令原话留痕：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗追认「授权00可以签收所有过程文档」）· HG-GRAPH-MODULES=approved（图谱新签义务随 30 交付由 00 收口代录）  
> **机械复核**：`npx spec-wave verify` PASS（2026-09-23）· `task lint` PASS  
> **task**：`docs/tasks/active/task_host_v1_delegation_token.md`（active · R1 PASS-WITH-NITS · N1–N5 已微修留痕）  
> **SPEC**：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（signed · Q1 HMAC-SHA256 / Q2 只读自动·其余 HITL / Q3 不新增一级模块 锁死）

## 30 执行要点（完整 Prompt 已下发子 Agent · 要点留痕）

1. 先切分支 `task/host-v1-delegation-token`（禁 master/main 直改）；首输出 GATE_VERIFY 表。
2. 实现序 D1 令牌模型（`capability/delegation.py`）→ D5 requested_scope（subtasks schema + Builder 声明∩裁剪）→ D2 签发点（subtask_join 分发 · 审批口径 · 签发序号/supersede · env 密钥纪律）→ D3 验签门（`_prepare_call` lookup 前 · `_delegation_required` 口径 · 六类拒绝 ok=False 不落回执 · 三档模式 off 默认）→ D4 审计（记动作不记内容）→ D6 测试（两个新测试文件 + 变异检验三条）。
3. 非范围红线：零新表/列 · 零新路由 · SSE 零新事件 · 不改 freeze · 不新增一级模块 · 不改六道闸既有语义（形态偏离 → 停 30 回炉补闸）。
4. 验证：`.venv/bin/python -m pytest tests` 全绿（基线 1368 · 无既有用例删除）+ `ruff check app tests` 绿；B1 八组逐条回填。
5. commit 在任务分支；**不 push · 不开 PR · 不 merge**（00 收口：40 → PR+CI 绿+merge → 图谱回写 00 代录 HG-GRAPH-MODULES → CLOSE）。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 30 棒 invoke 落盘 + 委派子 Agent（闸全绿 · verify PASS 后下发） |
