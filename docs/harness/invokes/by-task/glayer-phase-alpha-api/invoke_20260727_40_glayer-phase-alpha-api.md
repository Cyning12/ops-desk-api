# Invoke：40 自检 · glayer-phase-alpha-api

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 40-self-check |
| task_slug | `glayer-phase-alpha-api` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_glayer_phase_alpha_api.md` |
| related_review_or_none | `docs/harness/reviews/task_glayer_phase_alpha_api_audit_R1_20260727.md` |
| git_branch | `task/glayer-phase-alpha-api-v1` |
| worktree_root | — |
| created_utc_or_local | 2026-07-27 |
| notes | **补录**：30 执行后补跑 40；证据以本回合重跑命令为准。 |

---

## 可复制 Prompt 快照

```text
## 40 自检

@docs/tasks/active/task_glayer_phase_alpha_api.md
@docs/harness/prompts/40-self-check.md

逐条对照验收标准；必须运行：
  ./scripts/graph-compile.sh
  npx @cyning/harness verify --target . --task docs/tasks/active/task_glayer_phase_alpha_api.md
  find docs/_tech_graph/{l0,l1,l2,shared} docs/skills -type f | sort

回填 task「### 自检结论（执行者）」；fail 则回 30。
```

---

## 交付摘要（本帽结束时填）

### 验收表

| 验收项 | 结果 | 证据 |
|--------|------|------|
| 存在 l0/l1/l2/shared 与 docs/skills s-l0/s-l1 | pass | 目录树见下 |
| 模块真值在 l1/01_modules.md；AGENTS 闸路径已更新 | pass | `AGENTS.md` 指向 `l1/01_modules.md`；根 stub 存在 |
| chat G-L2 indexes 可反查 | pass | `l2/indexes/by_path.yaml` · `by_symbol.yaml` |
| `./scripts/graph-compile.sh` 绿 | pass | 退出码 0；OK×4 graphs |
| 正文无裸架构义 L0/L1/L2（目录/历史除外） | pass | LAYER_README / 消歧约定；stub 标明历史裸号 |

### 验证命令

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `./scripts/graph-compile.sh` | 0 | 4 graphs compile+check OK；shared/graph.json 生成 |
| `npx @cyning/harness verify --target . --task docs/tasks/active/task_glayer_phase_alpha_api.md` | 0 | VERIFY: PASS；无 invoke gap |
| `npx @cyning/harness task lint --file docs/tasks/active/task_glayer_phase_alpha_api.md` | 0 | ok=true（仅 W4 思考轮豁免） |
| `test -f docs/_tech_graph/l1/01_modules.md && test -f docs/skills/s-l0-project-map/SKILL.md` | 0 | 真值文件存在 |

### 已知未测 / 非范围

- 未跑全量 `pytest`（task：`code_quality_bar=not_applicable`；无业务改码）
- web/ios 分层、cyning-harness 回灌不在本 task

### 下一棒

交还 00 / 维护者：审 diff → commit/PR；Phase β 另开 task。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-27 | 补录 40 自检 invoke |
