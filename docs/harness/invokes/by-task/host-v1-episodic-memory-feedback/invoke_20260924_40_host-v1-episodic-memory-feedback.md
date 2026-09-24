# Invoke · 40（核验 + PR）· host-v1-episodic-memory-feedback（V1-D）

> **日期**：2026-09-24  
> **帽**：40（**00 委派子 Agent** · 00 本窗未改 `app/`；图谱人签行已由 00 代录 `approved`）  
> **前置**：30-resume 收口（[V1-D 30-resume 收口](7c27abf6-c067-421f-b607-0789aa54fcaf) · commits `d4bc8d7`/`fec4f63`/`0c5b787`/`0a0e5bb` + 00 代录签 commit）  
> **工作目录**：`/private/tmp/opsdesk-wt-v1d` · 分支 `task/host-v1-episodic-memory-feedback`

## 40 必做

1. **独立核验**（不采信 30 口号）：新增三测全绿 · B1 相关回归抽核 · `ruff check app tests` 净增 0（对照 master）· `./scripts/graph-compile.sh` 绿 · alembic upgrade/downgrade 可逆抽核 · diff 白名单对拍 task D6。
2. 变异检验：确认 30 三条「破坏→必挂→恢复」证据（commit message / 测试锚点）；缺则补跑留痕。
3. **push** `-u origin HEAD` + **`gh pr create`**（title/body 对齐 V1-A/C 风格 · 含验收/测试计划）。
4. 盯 CI 至绿；**不代 merge**（等待 auto-merge 或维护者）；若需 ENABLE auto-merge 可按仓先例。
5. 回写本 invoke：pytest/ruff/graph 摘要 · PR URL · CI 态。**CLOSE 归档留给 00**（merge 后）。

## 非做

- 不改业务语义 / 不扩非范围  
- 不归档 `done/`（00 CLOSE）  
- 不启动 V1-E

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 40（图谱已 00 代录 approved · 委派核验+PR） |
