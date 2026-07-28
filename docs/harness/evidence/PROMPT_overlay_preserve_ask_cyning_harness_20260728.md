# PROMPT · 交产品仓 · overlay 冲刷能否根治（U2）

> **用途**：整段复制到 **cyning-harness** Open Folder 会话。  
> **来源**：ops-desk-api dogfood · FEEDBACK 2.20 / 复检 2.21 · 2026-07-28  
> **非范围**：本文件不改产品仓；由产品维护者评估与排期。

---

## 复制区（整段粘贴）

`````text
你负责产品仓 cyning-harness。请评估：消费者仓「每次 upgrade 后 overlay 被冲、须人工恢复」能否在产品侧完全根治；给出可落地结论（能 / 不能 / 部分）与方案取舍。

【Open Folder】
对准 cyning-harness 仓库 git root（勿写死 Desktop/Projects 假路径）。

【背景 · 消费者证据】
- 仓：ops-desk-api（preset fullstack-node-py · WikiTrack 已启用 · G-L 试点）
- 复现：npx @cyning/harness@2.20.0|2.21.0 upgrade --yes 后必现
- 被冲文件与内容：
  1) AGENTS.md（cyning-harness:begin/end marker 内）：丢失「pre-30 invoke 缺失 → 拒改码」句；丢失关键词 HG-PILOT-OPSDESK-GLAYER / G-L0
  2) docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md：HG-GRAPH-MODULES 占位从仓内定制「l1/01_modules」回退为产品默认「01_struct」
- CLAUDE.md / .cursor/rules/05-harness-starter.mdc：同波常无 diff（或 merge 后等价）
- 现状缓解：RUNBOOK_upgrade_wiki_delta §1.2 要求 upgrade 后 git diff 四文件并手恢复（2.21 已吸收为文档纪律，行为未消）
- 证据路径（只读对照，勿改 ops 仓除非另开 task）：
  - ops-desk-api/docs/harness/evidence/FEEDBACK_harness_2_20_0_from_ops_desk_api_20260728.md（U2）
  - ops-desk-api/docs/harness/evidence/FEEDBACK_harness_2_21_0_recheck_from_ops_desk_api_20260728.md

【问题（须回答）】
1. 根因分类：marker merge(replace) vs prompts 全量 sync vs 二者叠加？指出具体脚本/适配器路径。
2. 「完全解决」可行性：能否让带仓内定制的消费者 upgrade 后零人工恢复、且不丢产品侧 prompts/adapter 更新？
3. 若不能完全解决：最大可自动化到哪一步（例如：三方合并、定制块 preserve、.overlay.patch、upgrade --preserve-local、仅 WARN 列出冲突 hunk）？
4. 对 G-L 试点仓：FRAGMENT 占位「l1/01_modules」是否应成为产品变体/profile 开关，而非每次被 01_struct 覆盖？
5. 兼容与风险：方案是否削弱 S2（不覆盖 docs/tasks）、是否增加 upgrade 自绊 S5、对无定制仓是否零行为变化？
6. 结论表（必填）：

   | 结论 | 理由 | 建议版本/里程碑 | 非目标 |
   |------|------|-----------------|--------|
   | 能完全解决 / 部分解决 / 不能（保持 §1.2） | … | 例如 2.22.x 或 wontfix | … |

【约束】
- 禁擅自 npm publish；改动走产品仓 task + PR。
- 不削弱 close / wiki_delta / pre-30 闸语义。
- 先读真值：wizard sync/upgrade、ide adapters merge、harness/prompts 拷贝策略、RUNBOOK §1.2、CHANGELOG 2.21.0 overlay 条目。
- 若需改码：先出设计摘要与 failure_paths，再等维护者签闸；本 Prompt 默认只要「确认结论 + 方案草图」，除非维护者明示开工实现。

【验收（本会话）】
- 根因路径引用到具体文件/函数（或脚本名）。
- 明确三选一结论：完全解决 / 部分解决 / 保持纪律。
- 若「完全/部分」：列出最小变更面（文件清单级）与回归用例（定制仓 + 无定制仓各一）。
- 若「保持纪律」：说明为何产品行为不可根治，以及 §1.2 是否还需补强（例如 upgrade 结束自动打印 diff 提示）。
`````

---

## 维护者备注（勿粘贴）

- 调度侧可将本 Prompt 与 web FEEDBACK 一并给产品 00/30。
- ops 仓本波无义务等产品根治后再关账；§1.2 纪律已够用。
