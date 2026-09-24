# Invoke · 30（改码 · 委派子 Agent）· host-v1-episodic-memory-feedback（V1-D 波）

> **日期**：2026-09-23  
> **帽**：30（**00 委派子 Agent 执行** · 00 不亲自 30）  
> **闸态（下发时真值）**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **approved**（00 代录 · 维护者令原话+本窗双令留痕）· `npx spec-wave verify` PASS · task lint PASS  
> **task**：`docs/tasks/active/task_host_v1_episodic_memory_feedback.md`（active）· **SPEC**：`docs/spec/host-v1-episodic-memory-feedback/SPEC-host-v1-episodic-memory-feedback_v0.md`（signed）

## 30 执行要点（完整 Prompt 已下发子 Agent · 要点留痕）

1. **worktree 隔离**（承 B/C 并行先例）：唯一工作目录 `/tmp/opsdesk-wt-v1d`（已检出 `task/host-v1-episodic-memory-feedback` · 含 .env）；主树只读文档+借 venv；禁 master 直改。
2. 实现序 D1 表+迁移（**本波唯一 alembic** · 可逆 · off 态 drop 安全）→ D2 episode_gate/episode_service（U4 零互写 · 闸五判据含 class 词表合法 · import 守护）→ D3 `[相似经验]` 独立分节（双开关默认关 · 三闸预算）→ D4 scripts/episode_pattern_mine.py（指纹规则 · 阈值≥3 · 确定性可重放）→ D5 建议面（零自动回写 git 守护）→ D6 断言+变异检验三条。
3. 非范围红线：零第二张表 · 零新路由/SSE 事件 · 不改 freeze/事实记忆既有语义 · 自动回写/实时聚类/subtask 级/embedding 全不做。
4. 验证：pytest（主仓 venv 绝对路径 · 基线 1420 · PG 用例本地 skip 形态如实标注 CI 有 PG）· ruff 净增 0 · B1 6+1 组逐条回填 · 不 push/不 PR。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 30 棒 invoke 落盘 + 委派子 Agent（闸全绿 · verify PASS 后下发 · worktree 隔离） |
