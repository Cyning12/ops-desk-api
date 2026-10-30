# fix-hitl-observe-node-config-injection 审查（R1 · 20-task-audit 存量回填）

> **审查对象**：`docs/tasks/done/task_fix_hitl_observe_node_config_injection.md`（v1.0 · 已归档 done/）
> **审查帽**：20-task-audit（R1 · 存量回填补审 · 依 `docs/tasks/active/task_api_legacy_reviews_backfill.md` v0.4 缺口①）
> **日期**：2026-10-30
> **补审背景**：本 task 交付期仓级 reviews 机读扫描（spec-wave verify review-gates）尚未启用，R1 审查文当时未落盘，仓级扫描判缺口「missing R<n>」；按本轮回填 task 纪律补审落盘，不走豁免。
> **核对材料**：done task 原文 · 收尾文档 `docs/tasks/close/close_fix_hitl_observe_node_config_injection_20261028.md` · 交付 commit 链（PR #296 · squash 27fd930 · `git merge-base --is-ancestor 27fd930 master` 实证在 master）· 现行代码抽查（本帽 2026-10-30 亲验）
> **纪律声明**：事后补审不改 task 与交付实质内容；范围/验收/failure_paths 逐条对照交付实证核对，结论据实。

## 一、范围与非范围核对

| task 声明 | 交付实证 | 裁定 |
|---|---|---|
| observe_node 签名回退 `Optional[RunnableConfig]`（最小面修复） | 现行 `app/ops/lg_rag/multi/nodes.py:2156`：`async def observe_node(state: LgRagState, config: Optional[RunnableConfig] = None) -> dict:  # noqa: UP045`（亲验） | ✅ 一致 |
| `# noqa: UP045` 与签名同 commit（failure_paths 第 1 条互锁） | squash 27fd930 同档同改（close 文档留痕） | ✅ 一致 |
| 形态钉 + 行为钉双测 | `tests/test_hitl_observe_config_injection.py` 现存于仓（亲验） | ✅ 一致 |
| 非范围：不改 ruff 规则集 · 不批量改写其它节点 | close 文档 diff 面仅 nodes.py + 钉测两档，零越界 | ✅ 一致 |

**根因与修复对因核对**：task 钉案根因——PR #274（b73bb8a ruff 批量改写）将 observe_node 签名改为 `RunnableConfig | None` 且文件带 `from __future__ import annotations`（nodes.py:14），langgraph 1.x 因注解形态不注入 config → HITL 审批单 thread_id 空 → resume 409（判定点 `app/ops/hitl/router.py:436` 只查 thread_id）。修复回退签名形态，机制对因；非症状性打补丁。

## 二、验收标准与交付一致性

| 验收 | 实证 | 裁定 |
|---|---|---|
| 1. 形态钉测绿（源码断言签名形态，`RunnableConfig | None` 出现即红） | 钉测文件现存；close 文档录 CI 4/4 绿 | ✅ |
| 2. 行为钉测绿（supervisor 图带 thread_id 跑至 HITL interrupt，落库审批单 thread_id 非空；先红后绿钉） | 钉测文件现存；close 文档录修复前先红实证 | ✅ |
| 3. `.venv/bin/ruff check app tests` 绿（钉版 0.15.21）+ pytest 全量不引入新红（28 红基线口径） | close 文档录 ruff/pytest 实证输出 | ✅ |
| 4. 40 live：run 1039c1a9 新审批单 thread_id 非空 → POST /resume 200 → t2 testing.write.echo 实际执行 → done{resumed} | close 文档录 live 验收 PASS | ✅ |

## 三、failure_paths 核对

- **UP045 反咬**（无 noqa 的 `Optional[RunnableConfig]` 必被 ruff 判红）→ noqa 与签名同 commit + 形态钉拦截：交付落实 ✓
- **`ruff --fix` 无视注释自动改写** → noqa 条目 --fix 不动 + 钉测双保险：落实 ✓
- **行为钉须先红后绿**（防恒绿摆设）→ close 文档录修复前先红：落实 ✓
- **其它同形态受害节点** → task 附全仓扫描结论，交付说明未列新增受害面：落实 ✓
- **存量 approved 空 thread_id 单据 resume 仍 409（设计内防呆，非回归）** → 复跑新 run 验收、不追旧单，与 close 口径一致：落实 ✓

## 四、结论/签收

本帽裁定：本 task 审查 **PASS**。验收 4 条与交付逐条一致，范围与非范围零漂移，failure_paths 五条防护全部落实；交付 commit 27fd930（PR #296）已在 master 实证且 CI 全绿，现行代码抽查（nodes.py:2156 签名形态 + 钉测文件存续）与 task 声明一致。核对全程未发现历史交付的实质问题，零内容阻塞项遗留。HG-AUDIT-R1 当时维护者签收（task 人工闸表 m00627 转录）与本审查结论相容；本件为存量回填审查，既有闸态照登不重签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 20 R1 存量回填补审落盘（task_api_legacy_reviews_backfill v0.4 缺口①）：done task + close 文档 + PR #296 交付链 + 现行代码抽查逐条核对，裁定 PASS，零实质问题 |
