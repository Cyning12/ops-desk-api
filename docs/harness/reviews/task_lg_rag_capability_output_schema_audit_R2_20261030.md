# lg-rag-capability-output-schema 审查（R2 · 20-task-audit 存量回填补轮）

> **审查对象**：`docs/tasks/done/task_lg_rag_capability_output_schema.md`（v1.1 · R1 缺口回填后 · 已归档 done/）
> **审查帽**：20-task-audit（R2 · 存量回填补轮 · 依 `docs/tasks/active/task_api_legacy_reviews_backfill.md` v0.4 缺口③）
> **日期**：2026-10-30
> **补轮背景**：原 R1 已落盘但其结论节含机读契约否定字面，仓级扫描判「结论不可机读」；按「不通过 → 补轮 R+1」纪律补本 R2。R2 落盘即唯一被评估轮（review-gates 最高轮语义），原 R1 留档不参与判定。
> **核对材料**：done task v1.1 原文 · 原 R1 `docs/harness/reviews/task_lg_rag_capability_output_schema_audit_R1_20261027.md` · 收尾文档 `docs/tasks/close/close_lg_rag_capability_output_schema_20261028.md` · 交付 commit 链（回填 8cd8584 · PR #294 squash bfed4cd · 均 `git merge-base --is-ancestor` 实证在 master）· 现行代码抽查（本帽 2026-10-30 亲验）
> **纪律声明**：事后补审不改 task 与交付实质内容；结论据实。

## 前审沿革（R1 → 回填 → 交付）

原 R1（2026-10-27）裁定 BLOCKED：阻塞项 B1——task 范围漏 `builtin.v1.yaml` 主加载面（`ensure_default_capabilities`，defaults.py:159-173 运行期优先读 YAML），另 N1–N6 非阻塞观察。R1 结论节含「内容阻塞」否定字面，命中仓级机读契约否定守卫 → 判不可机读（本 R2 补轮动因）。后续沿革：10-task 将 B1/B1'/N1/N2/N4 回填 task v1.1（commit 8cd8584 · 验收 3 扩为「对拍对象必须是运行期实际生效的注册表——覆盖 builtin.v1.yaml 主路径」）→ HG-AUDIT-R1 维护者签收 → 30 交付 PR #294（squash bfed4cd · CI 4/4 绿）→ close 文档录验收 5 条全 PASS（含 ⑤ 40 live run 1039c1a9 t1 produces 收敛真实字段），§四.1 对 R1 BLOCKED 照登留痕。

## 一、R1 阻塞项闭环核对

| R1 项 | 闭环实证 | 裁定 |
|---|---|---|
| **B1** 范围漏 builtin.v1.yaml 主加载面 | task v1.1 验收 3 已扩为运行期注册表对拍（覆盖 builtin.v1.yaml 主路径，文内注明「R1 审查 B1' 回填」）；交付 `tests/test_capability_output_fields.py` 现存于仓（亲验） | ✅ 闭环 |
| N1/N2/N4 非阻塞观察 | 同 commit 8cd8584 回填 task v1.1 | ✅ 闭环 |

## 二、范围/验收/failure_paths 与交付一致性

| 核对点 | 实证 | 裁定 |
|---|---|---|
| 范围：CapabilitySpec 增 `output_fields: tuple[str, ...] = ()`（planner 字段名清单 · 与既有 output_schema 运行期契约分工） | 现行 `app/ops/capability/types.py:122` `output_fields: tuple[str, ...] = ()`（亲验 · :118-120 注释分工口径） | ✅ 一致 |
| 范围：三加载面回填（builtin.v1.yaml / defaults.py / testing.v1.yaml） | `app/ops/capability/manifests/builtin.v1.yaml` 现存 5 条 output_fields（:27/:47/:67/:90/:113 · 亲验）；testing.v1.yaml 同目录在册 | ✅ 一致 |
| 验收 1：catalog prompt 块含清单 · 未声明能力行逐字节零 diff | close 文档录 PASS | ✅ |
| 验收 2：清单外字段裁剪 + 留痕断言 · 清单内零 diff | close 文档录 PASS | ✅ |
| 验收 3：防漂移钉对拍运行期注册表（B1' 回填口径） | close 文档录 PASS · 测试档现存 | ✅ |
| 验收 4：钉版 ruff 0.15.21 绿 + pytest 不引入新红（28 红基线） | close 文档录实证 | ✅ |
| 验收 5：40 live d3a49 场景复跑，t1 produces 收敛真实字段、t2 write 执行成功 | close 文档录 live PASS（run 1039c1a9） | ✅ |
| failure_paths：声明漂移 → 验收 3 对拍拦截 + B 层 detail 清单最终防线 | 机制在册且交付一致 | ✅ |
| failure_paths：MCP/远端能力空声明不校验、退回现状不退化 | 默认空值口径与 types.py:122 一致 | ✅ |
| failure_paths：catalog prompt 变长 token 成本 → 仅字段名清单 | 交付口径一致 | ✅ |

## 三、结论/签收

本帽裁定：本 task 审查 **PASS**。R1 唯一阻塞项 B1 经 task v1.1 回填（8cd8584）与交付对拍钉闭环；验收 5 条与交付逐条一致（含 40 live 实证），范围与非范围零漂移，failure_paths 三条全部落实；交付 commit bfed4cd（PR #294）已在 master 实证且 CI 全绿，现行代码抽查（types.py:122 · builtin.v1.yaml 五面声明 · 测试档存续）与 task 声明一致。核对全程未发现历史交付的实质问题，零内容阻塞项遗留。本轮结论节按机读契约干净书写，前审沿革已独立成节另述；既有闸态照登不重签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 20 R2 存量回填补轮落盘（task_api_legacy_reviews_backfill v0.4 缺口③）：R1 B1 闭环核验 + 验收 5 条与交付一致性逐条核对 + 现行代码抽查，裁定 PASS，零实质问题；前审沿革独立成节 |
