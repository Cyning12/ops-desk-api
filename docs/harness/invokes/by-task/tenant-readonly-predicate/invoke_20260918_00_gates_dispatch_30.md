# invoke · 00 · tenant-readonly-predicate · 闸扫描 → 派 30

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-18 |
| **帽** | 00 |
| **分支** | `task/tenant-readonly-predicate`（从 `master` 建；WIP 已收进，未 silent 丢改） |
| **签注** | Fixture 轨 · 维护者令本地 30 · 闸表已 approved |

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | Y | 可 |
| HG-AUDIT-R1 | approved | approved | Y | Y | 可 |
| HG-GRAPH-MODULES | approved | approved | Y | Y | 可 |
| HG-STAGE-T-DATA | approved | approved | Y | Y | 可 |
| HG-CONTRACT-FREEZE | approved | approved | Y | Y | 可 |

reviews：Fixture 轨 · **不写长审** · `verify --allow-no-review` 豁免留痕  
pre-30 invoke：缺 10/20 · `verify --allow-invoke-gap` 豁免留痕（本窗仅落 00；仍建议 CLOSE 前补快照）

机械：

```text
npx spec-wave verify --target . --task docs/tasks/active/task_tenant_readonly_predicate.md \
  --allow-no-review --allow-invoke-gap
→ VERIFY: PASS
```

结论：**可进入 30 读码/改码**（Fixture · 本地跑通）

## WIP 交接（根窗停工点）

已绿：`pytest tests/test_tenant_context.py + tests/test_capability_lookups.py` → 18 passed（前提 tenant_id 列存在）  
未完：T5 图谱备注、checklist 勾选、本机非 Docker api 验收、T3 RAG 独立负样本若缺、invoke 实录

## 下一棒

派 **30** 续作 WIP（勿重写）：迁移语义 + 谓词 + 上下文 + 负样本测绿 + 本机 api 验收 + checklist/invoke。  
禁止：生产 B 种子、改 web、改 SSE freeze、改 `chat/graph.py`、未令 commit/push/PR。

## 本窗

**未改实现码** · 已派子 Agent：**30**
