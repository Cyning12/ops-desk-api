# Invoke · 30（改码 · 委派子 Agent）· host-v1-visibility-scenario-policy（V1-B 波）

> **日期**：2026-09-23  
> **帽**：30（**00 委派子 Agent 执行** · 00 不亲自 30）  
> **闸态（下发时真值）**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **approved**（00 代录 · 维护者令原话留痕：「签收……授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗双令）· `npx spec-wave verify` PASS · task lint PASS  
> **task**：`docs/tasks/active/task_host_v1_visibility_scenario_policy.md`（active）· **SPEC**：`docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md`（signed）

## 30 执行要点（完整 Prompt 已下发子 Agent · 要点留痕）

1. 先切分支 \`task/host-v1-visibility-scenario-policy\`（master 已含 V1-A）；untracked 过程文档不提交（00 收口）· commit 只含 app/+tests/。
2. 实现序 D1 intent_fallback channel → D4 四字段（schema+加载校验三硬规则+三档派生+builtin 补齐）→ D2 scenario_trim 纯函数（S1–S5 规则表 · 畸形 intent 安全默认）+ **双落点接线**（Builder 内 stage 2 · supervisor nodes.py:933-948 交集输入改有效可见集 · SPEC R1 B-1 澄清钉死）→ D3 剔除台账 → D5 断言+变异检验三条。
3. 非范围红线：零新表/路由/SSE 事件 · 不改 freeze/IntentV1/03 prompt/baseline 语义 · HITL 三档不做 · 会话上下文不入键。
4. 验证：pytest 全绿（基线 1420 · 11 红基线环境性可证）· ruff 净增 0 · B1 六组逐条回填 · 不 push/不 PR。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 30 棒 invoke 落盘 + 委派子 Agent（闸全绿 · verify PASS 后下发） |
