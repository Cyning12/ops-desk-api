# invoke · 40 验证 · p2c-t1-planner-tool-awareness

> **task_slug**：p2c-t1-planner-tool-awareness
> **日期**：2026-11-17

## 内容

40 全量验证与逐签对照：目标回归七件 · 全量 pytest（真 PG 五键 blank · 三轮）· base b8d11262 同路径基线对照 · ruff · 冒烟实测（预算/空目录/泄漏）。

## 验证台账

| 检查 | 结果 |
|------|------|
| 目标七件 pytest（真 PG 五键 blank） | **103 passed** 零红 |
| 全量 pytest 第 1/2/3 轮 | 26 failed / 2430 passed / 3 skipped（失败集三轮逐件一致 · 确定性非随机抖动） |
| base b8d11262 同路径基线（stash 全量） | 25 failed / 2427 passed / 1 skipped |
| 失败集 diff（branch vs base） | **唯一增量 = test_wave_gate_registry**（脏树期结构性红：在途 nodes.py 只在本波 active entry 白名单 → closed 波报禁改面触碰 · 委派书钉明常态 · 提交后闭窗复跑 + CI 终裁）；其余 25 件逐件一致（全量期并发/注册表污染型环境性红 · 单跑/子集跑转绿：test_multi_replica_dualproc 单跑 9 passed · 采样 5 件中 4 件子集复跑转绿） |
| skipped 差异 +2 | TC8/TC5 白名单闸因本波在途文件（registry.yaml · 三测试件）入其越界清单转「使命完成」skip 分支——结构性 · 合并后回常 |
| ruff check app tests | All checks passed（exit=0） |
| 预算锚实测 | 默认 9 条目录 _build_catalog_block 全长 **4186 ≤ 6000**（§6.5） |
| 空目录实测 | _build_catalog_block([]) = 「（当前无可用 local_fn 工具）」零追加 |
| 泄漏实测 | _TOOL_AWARENESS_GUIDANCE 对默认 registry 全 capability id 扫描零命中 |
| 自检结论回填 | task 档验收 9 条全 [x] + 自检结论/偏差/限制三节回填 |

## 偏差

FP 两测试预期构造迁移（intentional behavior change · 见 task 档偏差登记）；其余无偏差。

## 结果

40 验证完成 · 验收 9 条全绿（第 7 条全量面以 base 对照 + CI 终裁口径收口）· 进 feat PR。
