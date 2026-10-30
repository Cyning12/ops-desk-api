# invoke · 40 · verify · api-graph-anchor-profile-fix

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-30 |
| **帽** | 40（独立验收 · 不信 30 自报 · 逐项亲跑亲读） |
| **task** | `docs/tasks/active/task_api_graph_anchor_profile_fix.md`（v0.5 · chore） |
| **分支** | `task/api-graph-anchor-profile-fix`（验收时点 HEAD=2a455dc = 30 交付末 commit） |
| **前置** | f388ac3 实现 + 2a455dc docs · 30 invoke `invoke_20261030_30_implement.md`（minimal）在案 |
| **纪律** | 只验收不改实现 · 本地 commit 仅验收留痕 · push/PR 禁 · 维护者脏文件 `docs/arch-browser/dist/site-data.json` 全程未动 |

## 闸扫描（40 亲读 task 人工闸表）

| human_gate_id | task 表 status | 说明 |
|---------------|----------------|------|
| HG-TASK-DRAFT | approved | 00 代录 · 授权锚 m00500 |
| HG-AUDIT-R1 | approved | 00 代录 · m00500 · R1 审查文 task_api_graph_anchor_profile_fix_audit_R1_20261030.md 通过零阻塞 |
| HG-GRAPH-MODULES | n/a | graph_change_layer=none |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无试点面 |

## ① 全量亲读 diff（f96419a..HEAD）

`git diff f96419a..HEAD` 共 3 文件：`.cyning-harness/profile.json`（单行值 `"l1/01_modules"` → `"docs/_tech_graph/l1"`，其余字段零改）+ 30 invoke 新增 + 本 task 自检/修订记录回填。**实现面恰为 profile 单行，零其他**；无 app/、无图谱源档、无 reviews 面变更（R1 审查文系 f96419a 入库，不在 30 diff 内）。

## ② V1–V7 逐项复跑（亲跑实证）

| 验收 | 结果 | 40 亲跑实证 |
|------|------|------------|
| V1 profile 合法且可达 | ✅ | 值断言 EXIT=0 · `statSync('docs/_tech_graph/l1').isDirectory()` EXIT=0 · JSON.parse 通过；亲读 profile 全文：仅 graph_modules_path 一行异于我仓基线 |
| V2 本 task verify | ✅ | `npx spec-wave@3.5.0 verify --target . --task <本 task>` → EXIT=0 `VERIFY: PASS`；graph_anchor 行逐字：`verify: INFO · 图谱锚点引用检查 · 图谱锚点检查未生效（已跳过 · vocabulary_empty · 模块词表抽取失败（01_struct.md 缺失））`——与 30 照登逐字一致；`graph_path_unreachable` 计数=0。**独立取前基线**：f96419a detached worktree 同命令 → `已跳过 · graph_path_unreachable · graph_modules_path=l1/01_modules`，与 30 自报逐字吻合 |
| V3 存量回归 | ✅ | 基线法：`git worktree add` f96419a（同分支前置 commit · 同 task 档 + 旧 profile 值）。active `task_lg_rag_gate_produces_unfulfilled.md` 前后均 EXIT=2（HG-AUDIT-R1 pending）· done `task_specwave_upgrade_3_5_0.md` 前后均 EXIT=2（missing R<n> review）· **两档前后输出逐字节 diff 均为空**；基线两档输出零 graph_anchor 行（前置 BLOCKED 未达挂点，与 30 S3 说明一致） |
| V4 仓级裸 verify | ✅ | EXIT=2 照登不掩饰；reviews 缺口**恰 5 枚**与 FEEDBACK §5 基线一致：fix_hitl_observe_node_config_injection / fix_no_proxy_bracket_ipv6_sanitize（missing R<n> review）· lg_rag_capability_output_schema / query_coref_rewrite / supervisor_first_fail_closed（结论不可机读通过）；与 f96419a 基线仓级输出 diff 为空 · 无新增缺口类别 |
| V5 graph-compile | ✅ | `./scripts/graph-compile.sh` EXIT=0（真码非管道截断 · 输出 `done` 收尾）；`git status --porcelain docs/_tech_graph/` 空 |
| V6 task lint | ✅ | `npx spec-wave@3.5.0 task lint --file <本 task>` → `LINT: PASS` EXIT=0 |
| V7 diff 面 | ✅ | 见 ①：实现面 = profile 单行 · 留痕面 = invoke + task 文 · 零其他（维护者脏文件未入 diff） |

## ③ 波及面复核

- `grep graph_modules_path` 全仓：命中均为文档/留痕面（AGENTS.md · 本 task · 历史 task/reviews/FEEDBACK/invoke）；**码面现役消费者仅 spec-wave 包**：`node_modules/spec-wave/lib/checks/graph-anchor.js:26`（probe 读值）· `lib/cli/verify.js:507`（挂点输出）· `lib/cli-lifecycle.js:193`；`package.json` 工具链仅钉 `spec-wave: 3.5.0`——与 R1 审查文「现役波及面为零（除 probe）」实证一致。
- `.coding-kit/` 目录在案（pre-existing：backups/ + manifest.json · 未跟踪）但**无 profile.json**——S1「不新建 .coding-kit/profile.json」守约，无双层 profile 遮蔽面。
- AGENTS.md:122 托管块仅符号引用 `profile `graph_modules_path``（非硬编码路径）；:158 local 定制块硬编码 `docs/_tech_graph/l1/01_modules.md` 文件全路径、不随 profile 值联动——R1 实证维持，本次复核一致。

## ④ 30 落账面抽核

- invoke minimal 在案（闸扫描/执行记录/commit 链/结论四段 · 承 task_specwave_upgrade_3_5_0 精简形态先例，形态合规）。
- 自检 S1–S4 / V1–V7 回填质量：40 逐项亲跑结果与 30 自报**逐项吻合**（含 graph_anchor 行、修正前基线行两处逐字串一致；EXIT 码与缺口集合一致）。
- 措辞审（failure_paths 第 4 行）：自检与 invoke 均照登 `vocabulary_empty` skipped 且明示「仍不挡 · 未拔高为检查已生效」——守约 ✅。
- 修订记录 v0.5 在案，内容与交付 diff 一致。
- 小疵不挡：V7 行措辞「invoke/reviews 留痕」中 reviews 系泛指（R1 审查文实在 f96419a 入库），30 diff 内无 reviews 变更——表述宽泛但无误导，照登不改。

## ⑤ 遗留三条照登合理性

1. **vocabulary_empty 词表另案**：真判定需上游契约 `01_struct.md`「## 1. 模块边界表」节 + 首列反引号词表，本仓真值在 `01_modules.md`「## 模块表（必填）」节——新建/改节名均属图谱面新增（HG-GRAPH-MODULES 闸 · 非范围明示）→ 另案合理。
2. **存量锚点引用另案**：当前停于 vocabulary_empty skip，graph_anchor 未真判定 → 存量零新红（V3/V4 实证）→ 「若真判定后新红再另案」合理。
3. **合并裁决留维护者**：维护者令全程本地、push/PR 禁 → 本分支移交维护者裁决，照登合理。

## 结论

**PASS**：① diff 面纯净（实现面恰 profile 单行）· ② V1–V7 亲跑全绿且与 30 自报逐项吻合（含两处逐字串）· ③ 波及面复核成立 · ④ 30 落账合规 · ⑤ 遗留三条照登合理。诚实毕业（graph_path_unreachable → vocabulary_empty）实证成立，无退回项。
