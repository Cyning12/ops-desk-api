# 审查文：task_api_graph_anchor_profile_fix · 20-task-audit R1（2026-10-30）

> **审查帽**：20-task-audit（R1 · 维护者 2026-10-30 新原则首单：升级/流程类全走审查零豁免 · 禁 --allow-no-review）
> **对象**：分支 `task/api-graph-anchor-profile-fix`（HEAD db66bce）· `docs/tasks/active/task_api_graph_anchor_profile_fix.md`（v0.2 · 145 行）
> **审查方式**：书面审查 · 钉案逐条独立复核（亲读 node_modules/spec-wave@3.5.0 源码实证，不转述）· 不改 task 实质内容 · 闸一律不动 · 不 commit（本文留 untracked）
> **图谱锚点引用（面B 义务预演）**：本审查涉图谱面判断，锚点字面引用 `docs/_tech_graph/l1/01_modules.md` / `10_flow_*.graph.yaml` / G-L1 层。

## 一、结论摘要

| 维度 | 结论 |
|------|------|
| **内容审查** | **通过（零阻塞）**：钉案①②③④全部实证成立；验收 V1–V7 可机断；failure_paths 5 条覆盖写坏/误写/回归/措辞/越界；R0–R5 结构完整、early_stop at R4 理由成立 |
| **流程闸** | HG-TASK-DRAFT = approved（00 代录 · 授权锚 m00500 · v0.2 在案）；**HG-AUDIT-R1 = pending**（本审查文落盘后待维护者亲签 · 不代录）——30 拒开工态正确 |
| **机械复核** | `npx spec-wave task lint --file` → **LINT: PASS EXIT=0**；`verify --target . --task <本 task>` → **VERIFY: BLOCKED · HG-AUDIT-R1 pending**（预期态 ✓） |

## 二、钉案独立复核（读码实证）

| # | task 声称 | 实证结果 | 判定 |
|---|-----------|----------|------|
| 1 | 可达性判定 = `statSync().isDirectory()`（graph-anchor.js:30-40）· 目标必须是目录 | `node_modules/spec-wave/lib/checks/graph-anchor.js:33`：`reachable = statSync(graphPath).isDirectory();`（:30 resolve · :38-39 unreachable 返回） | ✅ 成立 |
| 2 | 词表源要求 `<dir>/01_struct.md` 含「## 1. 模块边界表」节（MODULE_SECTION_HEAD_RE） | graph-anchor.js:43 `MODULE_SECTION_HEAD_RE = /^##\s+1\.\s*模块边界表/`；:54-57 `extractGraphAnchorModuleVocab` 要求 01_struct.md 存在；:59-61 节匹配；judgeGraphAnchor（:214）:217-219 modules.ok=false → `skip vocabulary_empty` | ✅ 成立（行号引用小疵见 NIT-1） |
| 3 | 挂点 verify.js:498+ · invalid_json warn+skip 不挡（verify.js:500-502）· unreachable → INFO 一行 + skipped · exit 不变 | verify.js:498 probe 调用（invoke hats 步后/wiki-lint 前 · :488 注释「仅 --task 链接线」）；:500-503 invalid_json → stderr warn；:504-509 unreachable → `{ skipped: 'graph_path_unreachable' }` + INFO 行，无 exit 改动 | ✅ 成立 |
| 4 | 现状 profile 声明 `l1/01_modules` 相对仓根不可达 | `.cyning-harness/profile.json:5` = `"l1/01_modules"`；仓根 `ls l1` → No such file or directory；`.coding-kit/` 无 profile.json（仅 backups+manifest.json）→ resolveLayoutFile（cli-shared.js:126-134 · .coding-kit 优先 → legacy 兜底）落 legacy | ✅ 成立 |
| 5 | 修正值 `docs/_tech_graph/l1` 是目录且含 01_modules.md 与 10_flow_* 对 | `docs/_tech_graph/l1/` 在案：01_modules.md + 10_flow_*（6 对 .md/.graph.yaml）+ 11_flow_sync_to_chat 对；无 01_struct.md | ✅ 成立 |
| 6 | 修完毕业到 vocabulary_empty 仍不挡 | l1/ 无 01_struct.md → extractGraphAnchorModuleVocab :56-57 返 `{ok:false, '01_struct.md 缺失'}` → judgeGraphAnchor :217-219 skip vocabulary_empty → verify.js:529-533 INFO 行不挡 | ✅ 成立（路径契约链完整） |
| 7 | 本仓模块真值节名「## 模块表（必填）」 | `docs/_tech_graph/l1/01_modules.md:23` = `## 模块表（必填）`，不匹配 RE（RE 要求编号「1.」前缀） | ✅ 成立 |
| 8 | FEEDBACK 推测「改指 01_modules.md 文件路径」不成立 | isDirectory 硬拒文件路径 ✓；但推测出处在 FEEDBACK **§2:22**（遗留裁决项），§6 第 2 项仅回指 §2——task 行文「FEEDBACK §6.2」属间接引用（见 NIT-2） | ✅ 实质成立 |
| 9 | V4 基线「仓级 reviews 缺口 5 枚」 | FEEDBACK §5:37-38：3.5.0 与 3.3.0（master 0a5d610 worktree 复跑）同一 5 缺口逐字一致（fix_hitl_observe / fix_no_proxy / lg_rag_capability_output_schema / query_coref_rewrite / supervisor_first_fail_closed） | ✅ 成立 |
| 10 | 回归预断：修后存量 task verify EXIT 与缺口集合零新增 | 机制链：vocabulary_empty skip 只增 INFO 行不改 exit（verify.js:529-533）；且 01_struct.md 缺为本 task 交付后恒态（其创建在非范围）→ 真判定不可能被触发 → 存量 BLOCKED 风险构造性为零 | ✅ 成立 |

## 三、委托焦点逐项

### ② 词表另案 vs 同修（对照 web 仓 task_web_graph_anchor_profile_fix）

- **web 仓选择同修**：profile 指向 + `l1/01_struct.md` 词表源归位（真值自 01_modules.md 迁移 · HG-GRAPH-MODULES 闸随迁 · 根 stub 一跳到底 · D1–D7 定夺），目标 = 闸真生效、首件活体过闸。其 R1 论证「两重缺口互相独立，只修指向仍 vocabulary_empty」在技术上同样适用于本仓。
- **本仓选择另案**：只修可达性，交付「unreachable skip → vocabulary_empty skip」诚实毕业，词表面适配照登 S4 供维护者裁决。
- **评估：分叉可接受，理由三条**：
  1. **迁移涟漪不对称**：本仓 `docs/_tech_graph/l1/01_modules.md` 引用面数百处（tests/ 3 处硬编码路径 · scripts/graph_coverage_check.py:134 · arch-browser · skills · 历史 tasks/invokes 留痕），真值迁移是大手术；web 仓 8 模块、引用面小。同修在本仓不是「顺手」，是把 chore 膨胀为图谱迁移工程，双主题混审反而违审查纪律。
  2. HG-GRAPH-MODULES 闸纪律允许同 task 带闸做图谱面（web 即如此），故另案是**粒度选择非纪律强制**——但选择本身合理：chore 单行修正保持最小面，图谱面新增留待带闸专案。
  3. 代价已诚实照登：闸持续 dormant（vocabulary_empty）期间 graph_anchor 保护为零，task R2 residual_risks 与 S4 均未掩饰，维护者签收时可一并裁决另案优先级。
- **结论**：另案切分合理，不构成本 task 阻塞；建议维护者签 HG-AUDIT-R1 时一并对词表另案立项优先级表态（建议项 · 非阻塞）。

### ③ profile 真值位置与引用面 grep 影响面

- 真值唯一落点 `.cyning-harness/profile.json:5`（.coding-kit/ 无 profile.json · 读序 cli-shared.js:126-134 实证）。
- grep `graph_modules_path` 全仓：消费者仅 spec-wave probeGraphAnchor；AGENTS.md:122/:158 两处为 local 定制块内硬编码表述（指文件全路径 · upgrade 不改写区），不随 profile 值联动。
- 历史 FEEDBACK 记载的 @cyning/harness overlay 消费面（FRAGMENT graph_modules_path → l1/01_modules）属已退役工具链：package.json 现仅钉 `spec-wave: 3.5.0`，`docs/harness/prompts/` grep `l1/01_modules` 零命中。**值变更的现役波及面为零**，task 未单列该面不构成缺陷（实证在案 · 本条备查）。
- `l1/01_modules` 旧字面值在历史 done/invoke/reviews/FEEDBACK 中大量存续——task 非范围未明示「历史留痕不改」，但 V7 diff 面钉死单行变更已实质覆盖（观察项 · 非阻塞）。

### ④ 存量 task verify 回归风险的回退口

- 本 task 交付态下回归构造性不可能（见钉案 10）；failure_paths 第 3 条（存量被真判定新 BLOCKED → STOP 回维护者裁决）覆盖的是未来词表落地后的场景，属预案性质。
- 与 web 仓 D4（双 profile 一行 revert 即复归 dormant）相比，本 task 未明示「git checkout 复原 profile 单行即回退」这一 revert 级回退口——failure_paths 第 1 条对 JSON 写坏有「git checkout 复原重改」，可类推但未写成通用回退句（NIT-4）。

## 四、通用核对

- **验收可机断性**：V1 node 断言两行（值相等 + isDirectory）✓ · V2/V3/V4 verify 输出逐字对照 ✓ · V5 graph-compile EXIT ✓ · V6 lint ✓ · V7 diff 面枚举 ✓——全部可机断，无措辞拔高位。
- **failure_paths 完备**：写坏 / 误写文件路径 / 存量新 BLOCKED / 措辞拔高 / 越图谱面，5 条与范围逐项对应，各带处置与可见面 ✓。
- **非范围**：5 条，与本 task 最小面一致；「web 仓同题另案」与 §7 互引闭合 ✓。
- **思考轮 R0–R5**：控制表 + 逐轮小节闭合；R4 early_stop 理由（R0–R3 闭环 · 无残余分叉）与 chore 粒度相称；R5 标未开 ✓。
- **行为变更类「旧测 grep 影响面」提醒（K7）**：profile 值无测试/业务码消费者（tests/ 引用的是 01_modules.md 文件路径非 profile 值 · grep 实证），pytest 构造性恒等声称成立 ✓。

## 五、NIT 清单（非阻塞 · 10 回填时可顺手修）

| # | 位置 | 内容 |
|---|------|------|
| NIT-1 | task :42 | 「graph-anchor.js:54-57 judgeGraphAnchor 词表抽取要求…含『## 1. 模块边界表』节」——:54-57 是 `extractGraphAnchorModuleVocab` 入口与 01_struct.md 存在性判定；节 RE 在 :43、节匹配在 :59-61，judgeGraphAnchor 本体在 :214。实质正确，行号/函数名引用不精。 |
| NIT-2 | task :41 | 「FEEDBACK §6.2 推测」——文件路径推测实在 FEEDBACK §2:22（遗留裁决项），§6 第 2 项仅回指。建议改引 §2。 |
| NIT-3 | 章节编号 | 「## 4. 失败路径」之后「## 验收标准」无编号，再跳「## 6.」——缺 5 号（功能无碍：DECISION_SECTION_RE 对「## 验收标准」「## 4. 失败路径（failure_paths）」均匹配 ✓）。 |
| NIT-4 | failure_paths | 通用回退口（profile 单行 git checkout 复原 = 闸复归 unreachable skip 态）未明示成句，仅第 1 条 JSON 写坏场景有类似表述；对照 web 仓 D4 可补一句。 |
| NIT-5 | §7 关联 | 互引的 `task_api_prompts_sync_3_5_0.md` / `task_api_legacy_reviews_backfill.md` 在本分支不存在（分别在 task/api-prompts-sync-3-5-0 @25e02d3 · task/api-legacy-reviews-backfill @001a188 两姊妹分支），合并前为跨分支悬空引用；落一行「另分支在制」注记更稳。 |

## 六、回填清单

无内容阻塞回填项。NIT-1~5 由维护者裁决是否令 10 顺手回填（均不动实质）。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文 · 内容通过零阻塞 · NIT 5 条）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者亲签 · 日期 · 本 task 明文禁 00 代录）
- [ ] （建议）一并裁决词表面适配另案的立项优先级（S4 差距照登在案）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

**审查执行记录**：lint PASS EXIT=0 · verify BLOCKED 于 HG-AUDIT-R1 pending（预期）· 全程只读 + 本文落盘，task 文/闸/码零改动，本文留 untracked 待维护者处置。
