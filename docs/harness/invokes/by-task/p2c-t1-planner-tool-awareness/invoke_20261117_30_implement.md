# invoke · 30 实施 · p2c-t1-planner-tool-awareness

> **task_slug**：p2c-t1-planner-tool-awareness
> **日期**：2026-11-17
> **闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三行 approved（verify PASS）

## 内容

1. app/ops/lg_rag/multi/nodes.py：
   - 新增 `_TOOL_AWARENESS_GUIDANCE` 静态常量（选择原则引导语 + 1 条泛化问法 JSON few-shot「现在几点了」→ type=tool + tool 占位 `<目录中对应工具的 capability_id>` + rag 兜底从句「仅当目录中没有工具能覆盖该问题时才纯 rag」· 269 字符 · 零 capability id）；
   - 新增 `_build_catalog_block(caps)` 唯一装配点：非空 caps 块首注入引导语，空 caps 原样返回占位文本零追加；
   - supervisor_node catalog 装配改调 `_build_catalog_block`（suffix/base 两路共用自动覆盖）；`_format_capability_catalog` 本体零改。
2. tests/test_lg_rag_supervisor_capability_catalog.py：扩 P2c-T1 回归基线六断言——空目录零追加 · 非空注入且行渲染保持（endswith 原渲染）· 引导语零 capability id 泄漏 · 预算锚 ≤6000 · mock LLM 捕获 system 含引导语+few-shot+rag 兜底从句（+few-shot 结构锚 type=tool/capability_id）· 窄 allowlist（utc_now_iso）引导语在且被隐藏工具不在。
3. FP 迁移：tests/test_hitl_approved_replan_quality.py（:209 区）与 tests/test_supervisor_replan_error_feedback.py（:252 区）预期构造改走 `_build_catalog_block(_fake_caps())`（intentional behavior change · 行渲染零 diff 口径不动）。
4. 图谱：docs/_tech_graph/l1/01_modules.md lg_rag 行（:35）补 P2c-T1 备注 + HG-GRAPH-MODULES 签收行（:47 · 承 :46 先例）。

## 验证台账

| 检查 | 结果 |
|------|------|
| ruff check app/ops/lg_rag/multi/nodes.py | All checks passed |
| 冒烟（python -c）：默认 9 条目录 _build_catalog_block 全长 | 4186 ≤ 6000 ✓ |
| _build_catalog_block([]) | 「（当前无可用 local_fn 工具）」零追加 ✓ |
| 引导语 capability id 泄漏扫描 | [] 零泄漏 ✓ |
| 目标七文件 pytest（真 PG · 五键 blank） | 103 passed |

## 偏差

无（§5-2 蒸馏裁定为委派书要求的评估输出 · 登记于 task 档 R3 而非实施偏差）。

## 结果

30 实施完成 · 进 40 全量验证。
