# invoke · diff-whitelist-anchor-drift · CLOSE（2026-11-06 · [00] 帽 · 照 `920c8e5` 先例）

## 五棒闭环（issue #337 链 · 同日全链）

1. **10 落稿**（PR [#357](https://github.com/Cyning12/ops-desk-api/pull/357) squash `0358c3b` · 维护者 comment `6682233401` 令 · 受理依据 13:40 多选授权）：task 档四闸 pending + A1 锚点语义专节 + 10 档诊断取证（两枚用例 2 failed 实测 + banned 溯源 `6c9d0e6`/`51030a4`）——`invoke_20261106_10_task_draft.md`
2. **20-R1 书面审 PASS**（PR [#358](https://github.com/Cyning12/ops-desk-api/pull/358) squash `172a780` · 维护者 comment `6683541162` 令）：六要素/闸表契约/A1 三要素全 PASS · **三子形态对拍**（①重钉 `_BASE` 与 `_WAVE_TIP` 回归牙窗口不相容拍否 / ②改固定波次窗语义正解 / ③调 `_allowed` 面拍否）· **F1 暗礁实测**（wave1 闭窗 2 件波内未登记面 · `920c8e5`）——审查文 `docs/harness/reviews/task_diff_whitelist_anchor_drift_audit_R1_20261106.md` + `invoke_20261106_20_audit.md` · 四闸随档全签（签录 `0870fb4` + status 单元格修复 `7748dfe`）
3. **30 实现红转绿**（PR [#359](https://github.com/Cyning12/ops-desk-api/pull/359) squash `18756ba` · GO = comment `6684073257`）：签认形态②三件套（固定波次窗语义 + F1 两件 00 裁定式登记 + N2 浅克隆退化规格）· 2 failed→2 passed 命令级双证据 · 闸语义对拍三实证 · 全量 2103 passed 零新增红——`invoke_20261106_30_implement.md`
4. **40 独立复跑机制面 PASS**（PR [#360](https://github.com/Cyning12/ops-desk-api/pull/360) squash `9e4c878` · 授权 = comment `6685019068`）：不采信 30 自报——两闸 2 passed 非转录 · 全量 2104 passed 零新增红 · **浅克隆 `--depth 1` N2 实证**（committed 面审计输出跳过 + banned 探针原样咬 · 行为链与签认规格逐字吻合）· 固定窗逐行审查（四锚值未动 · 闸语义零改动）——`invoke_20261106_40_verify.md` + 审查文 `docs/harness/reviews/task_diff_whitelist_anchor_drift_review_40_20261106.md`
5. **50 CLOSE 归档**（本档 · 授权 = comment `6686355563`）：active→done 迁档 + 全链 SHA 回填 + 本 invoke · docs-only PR

## 裁定链（00）

1. **设计闸裁决（HG-DIFF-WHITELIST-DIAGNOSIS · lead 签认 · review `5799605736` + GO `6684073257`）**：**whitelist 过期 → 刷新基线 · 子形态 = 改固定波次窗语义**——committed 面由 `_BASE..HEAD` 增长窗收窄为 `_BASE.._WAVE_TIP` 闭窗 + 工作区/暂存 vs HEAD 未提交面 + untracked · banned 前置只作用该面 · 四态/O2/回归牙原样保留 · 禁删闸禁豁免。证据链：四锚 rev-parse 全命中 + banned 溯源 `6c9d0e6`（specwave）/`51030a4`（stage-w）均钉锚后合法波次 + 20-R1 三子形态对拍。
2. **F1 两件 00 裁定式登记**（`920c8e5` 先例同性质）：`backups/…snapshot` + `task_query_coref_rewrite_review40_20261019.md`（前波次归属注明）逐路径登记入 `_TREE_ALLOWED_FILES` + 限定语——CLOSE commit 落盘面被回归牙咬出后补登记，非放宽。
3. **N2 浅克隆退化规格**：`_WAVE_TIP` 不可解析 → 带审计输出跳过 committed 面 · 绝不退化为 vs HEAD 增长窗（否则浅克隆复现结构性常态红）。
4. **闸表 status 单元格修复**（`7748dfe`）：签录 `0870fb4` 漏翻 HG-DIFF-WHITELIST-DIAGNOSIS status → 依 GO 评论补翻（纯记录修复 · 非自签 · 修复记录入闸表行）。

## 行为变化宣告（唯一有意变化）

两枚 diff-whitelist 闸由「增长窗 committed 面」转为「闭窗档案 + 在途守卫」：master 干净树上两闸自「常态红（banned 前置 fail）」转为「态① pass」；后续波次触碰 `scripts/`/`alembic/` 等不再使两闸转红（闭窗外）；在途（未提交/untracked）触碰禁改面仍即时 fail（O2 原样）。

## 遗留挂账（非本链责任 · 如实移交）

1. **2 枚 env 依赖既有红**（`test_embedder_failure_degrades_with_marker` / `test_hitl_cross_instance_resume` · CI skip 面）——全链各棒登记同形 · 本地基线 4 failed → 2 failed（本链销项 diff-whitelist ×2）· 余 2 枚治理另案。
2. **未来波次 committed 面审计须自注册新闸**（20-R1 N3 口径）——本闸使命完成转档案形态；同类守卫需求承 2026-10-20 三闸先例。
3. 浅克隆「脏树 + tip 不可解析」组合下回归牙保守 fail-closed（`_touched_in_wave` 既有契约）——真实 CI 干净树不受影响 · 语义维持 fail-closed 不修正。

## 质量门（50 棒）

| 项 | 结果 |
|----|------|
| `spec-wave task lint --file docs/tasks/done/task_diff_whitelist_anchor_drift.md` | LINT: PASS（零 warn） |
| `spec-wave task lint-wiki-delta --target .` | LINT-WIKI-DELTA: PASS（scope all · done/ 在扫面） |
| `ruff check app tests` | 零新增（50 棒 docs-only · 未触码面） |
| 两枚闸 @ 本分支干净树 | 2 passed（CLOSE 迁档零影响实证） |
| diff 面 | docs-only（task 档迁移 + 本 invoke）· `app/` `tests/` 零触碰 |

## 杂项

- **README 索引**：`docs/tasks/active/README.md` 无本档条目（10 落稿期未登记）——无清理面 · 本 invoke 照登。
- **issue #337 关 issue**：由 lead 执行（本棒不关）。
- 分支 `agent/337-diff-whitelist-task-5e3e38c2abdd` 移交 00 统一清理（本 CLOSE 不删任何东西）。
