# invoke · 30 · implement · api-graph-anchor-profile-fix

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-30 |
| **帽** | 30 |
| **task** | `docs/tasks/active/task_api_graph_anchor_profile_fix.md`（v0.4 · chore） |
| **授权** | 双闸 approved（00 代录 · 维护者授权锚 m00500）· 本地 commit 可 · push/PR 禁（维护者令） |
| **retention** | minimal（工具类零业务面 · task meta invoke_retention_profile=minimal · 承 task_specwave_upgrade_3_5_0 精简形态先例） |

## 闸扫描（GATE_VERIFY 真值 = task 人工闸表）

| gate | status | 依据 |
|------|--------|------|
| HG-TASK-DRAFT | approved | task 人工闸表（00 代录 · m00500） |
| HG-AUDIT-R1 | approved | task 人工闸表（00 代录 · m00500 · R1 审查文 task_api_graph_anchor_profile_fix_audit_R1_20261030.md 通过零阻塞） |
| HG-GRAPH-MODULES | n/a | graph_change_layer=none（仅 profile 指针 · 图谱源档零改） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |

→ 30 可开工。维护者脏文件 `docs/arch-browser/dist/site-data.json` 全程未动。

## 执行记录

1. S1 单行修正：`.cyning-harness/profile.json:5` `graph_modules_path` = `"l1/01_modules"` → `"docs/_tech_graph/l1"`（其余字段零改 · 不新建 .coding-kit/profile.json）。
2. 修正前后基线对照实证（V2–V4 · 逐字照登见 task 自检结论）：
   - 修正前本 task verify：`已跳过 · graph_path_unreachable · graph_modules_path=l1/01_modules`；
   - 修正后本 task verify：`已跳过 · vocabulary_empty · 模块词表抽取失败（01_struct.md 缺失）` · 零 `graph_path_unreachable` · VERIFY: PASS EXIT=0 —— 与 R2 预断逐字一致（诚实毕业 · 不拔高为「检查已生效」）。
   - 回归：active task_lg_rag_gate_produces_unfulfilled 与 done task_specwave_upgrade_3_5_0 verify 输出 diff 为空、EXIT 不变（2/2）；仓级 verify EXIT=2 · reviews 缺口恰 5 枚基线 · 前后 diff 为空。
3. V5 `./scripts/graph-compile.sh` EXIT=0 · `git status --porcelain docs/_tech_graph/` 空（图谱零意外 diff）。
4. V6 `npx spec-wave@3.5.0 task lint --file <本 task>` → LINT: PASS EXIT=0。
5. 引用面复核：grep `graph_modules_path` 全仓——现役消费者仅 spec-wave probeGraphAnchor；AGENTS.md:122/:158 local 块硬编码 `docs/_tech_graph/l1/01_modules.md` 文件全路径、不随 profile 值联动（R1 已实证 · 本次复核维持）；历史 FEEDBACK/invoke/reviews 旧字面值属留痕不改（非范围）。
6. S4 词表面适配差距照登不实施：vocabulary_empty → 真判定需上游契约 `01_struct.md` + 「## 1. 模块边界表」节 + 首列反引号词表；本仓真值 `01_modules.md`「## 模块表（必填）」节（图谱面新增须 HG-GRAPH-MODULES 闸 · 另案裁决 · 双真值风险照登）。

## commit 链

f388ac3（profile 单行修正）→ 本 commit（invoke + 自检回填 + v0.5）

## 结论

**S1–S4 / V1–V7 全绿 · 诚实毕业达成**：INFO 由 `graph_path_unreachable` 毕业至 `vocabulary_empty`（仍不挡 · 词表另案）。回退口备查：profile 单行 `git checkout` 复原即归原态。遗留（另案）：①01_struct.md 词表面适配（图谱面 · 待 HG-GRAPH-MODULES 闸）②存量 task 图谱锚点引用补齐（若真判定后新红）。
