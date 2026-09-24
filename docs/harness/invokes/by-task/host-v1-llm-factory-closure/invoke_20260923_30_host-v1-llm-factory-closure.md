# Invoke · 30（改码 · 委派子 Agent）· host-v1-llm-factory-closure（V1-C 波）

> **日期**：2026-09-23  
> **帽**：30（**00 委派子 Agent 执行** · 00 不亲自 30）  
> **闸态（下发时真值）**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **approved**（00 代录 · 维护者令原话留痕：「签收……授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗双令）· `npx spec-wave verify` PASS · task lint PASS  
> **task**：`docs/tasks/active/task_host_v1_llm_factory_closure.md`（active）· **SPEC**：`docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md`（signed）

## 30 执行要点（完整 Prompt 已下发子 Agent · 要点留痕）

1. 先切分支 \`task/host-v1-llm-factory-closure\`；**与 V1-B 并行**（文件面零交叠 · 本波仅 app/llm）。
2. 实现序 D4 TASK_TIER_FALLBACKS+resolve_fallback_chain+链校验+单价表 → D1 llm/budget.py（声明/预估下限/三档/进程内计数器）→ D2 耗尽降级链（degraded 标记跟数据走 · 链末端不伪造成功）→ D3 llm/infer_cache.py（只缓存结构化产物 · 版本入键 · 默认关）→ D5 Cost per Successful Task → D6 断言+变异检验三条。
3. 非范围红线：零新表/路由/SSE 事件 · 不改 freeze/provider 契约/usage 末帧纪律 · 终答不缓存 · 规则 DSL 不做 · 不截流。
4. 验证：pytest 全绿 · ruff 净增 0 · B1 5+1 组逐条回填 · 不 push/不 PR。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 30 棒 invoke 落盘 + 委派子 Agent（闸全绿 · verify PASS 后下发） |
