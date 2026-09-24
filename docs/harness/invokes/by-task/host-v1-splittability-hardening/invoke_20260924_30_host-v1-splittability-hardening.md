# Invoke · 30（改码 · 委派子 Agent）· host-v1-splittability-hardening（V1-E）

> **日期**：2026-09-24  
> **帽**：30（**00 委派子 Agent** · 00 不亲自 30）  
> **闸态**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **approved**（00 代录）· `npx spec-wave verify` 须 PASS  
> **task**：`docs/tasks/active/task_host_v1_splittability_hardening.md`  
> **SPEC**：`docs/spec/host-v1-splittability-hardening/SPEC-…_v0.md`（signed）+ D1 真值 `docs/spec/multi-replica-verify/SPEC-…_v1.md`  
> **分支 / 工作目录**：`task/host-v1-splittability-hardening` · `/private/tmp/opsdesk-wt-master40`（可另建隔离 worktree；禁 master 直改）

## 实现序（钉死）

1. **D2** import-linter + `.importlinter`（contracts←`01_modules` 出边）+ 白名单逐条理由 + CI job  
2. **D3** RegistryReader/Writer + 本地 dict 默认 + 调用点注入 + 对拍零 diff  
3. **D4** env 全仓清单文档 + 策略包 YAML schema v0 单面试点（建议 llm 档级）+ 优先级断言  
4. **D1** 双进程回归 + 边界清单补扫（≥ delegation nonce / llm budget / infer_cache · file:line）+ 报告/runbook 可复核 · **验证轨 app/ 零生产码 diff**  
5. **D5** 「发现即另开」条目（可空表）+ 变异检验 + 图谱按实判

## 红线

- 不重写 #165 双进程基建 · 不外置进程内状态 · 不远程注册中心 · 不全量策略搬家  
- 零 alembic / 零新路由/SSE / 零 freeze 动 · 顺手修 bug→D5 另开  
- 对拍零 diff · ruff 净增 0 · 基线 collect 真跑复核（承 1587）  
- **不 push 实现码到 master · 可 push 本分支 · 不开 PR**（40 做）

## Python

`/Users/cyning/Desktop/Ops-desk/ops-desk-api/.venv/bin/python`（主仓 venv）

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 30（AUDIT 代录 approved · verify 后开工） |
