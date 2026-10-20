# invoke：delegation-naming-boundary · 20_task_audit_R1 · 2026-10-20

- **hat**：20-task-audit（R1 书面审 · 只审不改 · 不代签 HG-AUDIT-R1）
- **对象**：`docs/tasks/active/task_delegation_naming_boundary.md`（draft v0.1 · 191 行 · commit `84a44ba`）
- **审查文**：`docs/harness/reviews/task_delegation_naming_boundary_audit_R1_20261020.md`
- **写入面**：仅审查文 + 本 invoke（零 task/SPEC/app/ 改动 · 未代签任何闸）

## 结论：conditional_pass（阻塞 0 · M1/M2/M3 签前修订建议）

| 委托重点 | 结论 |
|---|---|
| 门控锚点修正核验（R1-N3） | **成立**：master `31924af` 逐行实证——真门控 `nodes.py:903`（条件建索引）+ `:931`（guard-skip 块头 · :941-942 台账钩子在册）；`:970` 系签发审批门 `_delegation_issue_block_reason` 块头（:971 实证）同形 if 误并，不在解耦面；`:1271` 同理。照 R1 字面解耦 :970 将错误启用签发审批，校正必要 |
| FP-2 三牙 | 完备可机断（TC3 钩子 :941-942 实证 / TC4 逆牙对拍 / TC5 矩阵含 :970 照常断言 · 应急口 false 口径明 · 用户可见=是三层落位） |
| 锚点实测 | 27 条：命中 24 / 漂移 2（tests def :338→:339、:352→:353）/ 事实错误 1（「env 台账 delegation 未登记在先」——GUIDE :12-14 已登记三键） |
| banned 前置（TC8） | **确认方向正确无反效果**：蓝本 :659-660 置尾时态④ skip（:632）与第四态 skip（:654-657）均掩盖禁区触碰；前置化 fail-closed。实现注意：态④无 diff base，禁区检测须以 vs HEAD+untracked 兜底（nit N-a） |
| graph_change_layer=none | 成立（承 Q3 + :116 先例 · env 键非图谱元素 · 越出回炉回路在案） |
| N5/N6/N7 | 处置合理（N6 实证 :15 单次 import · N7 实证 SPEC :159 仍在 · N5 承 R1 备选口径） |

## M 项（签前修订 · 不改实质）

- **M1**：TC1×TC8 互斥——`tests/test_capability_testing_write.py:185/:412/:468` 三处注释残留落入 TC1 tests/ 面但不在 D1 改名面与 TC8 白名单 → D1+白名单补该文件（推荐）或 TC1 收窄符号级+豁免清单
- **M2**：TC1 豁免清单缺图谱历史行——`01_modules.md:116` 闸登记表历史行含旧名，落入 docs/_tech_graph/ 面 → 豁免清单补「01_modules.md 闸登记表既有历史回写行」
- **M3**：R1 轮 env 台账措辞事实错误 → 改「delegation 三键已登记 capability 段 · lg_rag 段补登记新键」

## 闸态

HG-SPEC-SIGNOFF=approved · HG-AUDIT-R1=**pending**（本帽不代签 · M 闭合后 00 依授权代签）· HG-GRAPH-MODULES=approved（口径写明）。人签前维持：30 拒开工。
## 七、v0.2 R2 复核记录（2026-10-20 · 20-task-audit R2=pass）

审查文：\`docs/harness/reviews/task_delegation_naming_boundary_audit_R2_20261020.md\`

| 复核项 | 结论 |
|---|---|
| M1（TC1×TC8 互斥） | ✔ 闭合（D1 :61 + TC8 :126 · 三注释坐标 master \`31924af\` 实测零漂移） |
| M2（TC1 豁免②闸登记历史行） | ✔ 闭合（:119） |
| M3（env 台账措辞） | ✔ 闭合（:76 + :166） |
| nits N-a/N-d/N-e | ✔ 吸收（:126/:73/:119）· N-b/N-c 维持不改（符合 R1） |
| 修订面无夹带 | ✔（\`39101d9..a892547\` 仅 task + 10 invoke · 闸表/范围/TC 语义零触碰） |

写入面：仅审查文 + 本 invoke 补记（零 task/SPEC/app/ 改动 · 未代签闸）。
