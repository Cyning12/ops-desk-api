---
hat: 10-task
task_slug: graph_json_freeze_date_pin
date: 2026-10-17
---

# invoke · 10-task 起草 · graph_json_freeze_date_pin（仓卫生 · graph.json freeze_id/generated_at 日期漂移收口）

## 落稿摘要

- 起草帽：子 Agent 10-task（00 委派 · 2026-10-17 · 承接 close_ci_specwave_pin_align_20261017.md §四·2 / §七·1 另立案）。
- 实证锚点：`scripts/graph_yaml_to_json.py:65-69` 以 `datetime.now(UTC)` 生成 `freeze_id`（`OPS_DESK_API_TECH_GRAPH_FREEZE_<YYYYMMDD>_V1` 日期段）与 `generated_at`；调用链 `scripts/graph-compile.sh:58-59` + `.github/workflows/tech-graph.yml:33`（CI 同漂移）；消费方 `docs/arch-browser/scripts/build_site.py:558-559` 纯透传、`docs/arch-browser/web/app.js:55` 纯展示（无格式解析）；先例 `docs/_tech_graph/shared/99_mermaid_protocol.md:137` md `generated_at` 已为 `sha256-<16hex>` 内容戳。
- 授权锚点：`docs/tasks/close/close_ci_specwave_pin_align_20261017.md` §四·2 照录日期漂移（20261014→20261017 · ci-pin 棒 6be8f3c2 实证 · 已 git checkout 恢复零混入）+ §七·1 建议另立 task 收口——本 task 即该另立案。
- 交付：`docs/tasks/active/task_graph_json_freeze_date_pin.md`（status: draft · TC-1~6 含双跑字节级稳定 + CI/本地一致断言 · FP-1~6 覆盖 freeze 校验语义破坏与旧 freeze_id 消费方兼容 · 人工闸 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending · 零 git 操作）。
- 方案自由度：三候选（内容 hash 派生 / env 注入 / git commit 时间）供 30 定案，硬约束=默认值确定性 + freeze_id 骨架兼容；偏离三候选须先回 10。
- lint：`npx --yes spec-wave task lint --file docs/tasks/active/task_graph_json_freeze_date_pin.md` → EXIT=0 · **LINT: PASS**（仅 W3 自检结论占位提醒 · draft 期合法照登）。
- 诚实照登：spec-wave check 是否对 freeze_id 有隐性格式断言未实证（列 FP-1，30 先实证再定案）；git commit 时间方案在 CI 浅克隆下的可行性未实证（R2/R3 留 30 核验）；dist/site-data.json 存量快照含旧 freeze_id（20261014），落定后与 graph.json 新值的对比口径留 30 裁定。

## 留 20 审要点

- 三候选方案自由度是否过宽（是否须 10 收窄为单案）· TC-1 双跑字节断言可机断性 · FP-1 freeze 校验语义闸的实证顺序（先实证后定案）是否足够硬 · `graph_change_layer=none` 判定（graph.json 为产出物一次性落定 diff 属合法交付）。
