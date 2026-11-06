# invoke · 20-task-audit R1 · diff-whitelist-anchor-drift（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `20`（task 书面审 R1 · 承 issue #337 维护者 comment `6683541162` 令） |
| task_slug | `diff-whitelist-anchor-drift` |
| task 文件 | `docs/tasks/active/task_diff_whitelist_anchor_drift.md`（master `0358c3b` = PR #357 squash 合并点） |
| 审查文 | `docs/harness/reviews/task_diff_whitelist_anchor_drift_audit_R1_20261106.md` |
| 分支 | `agent/diff-whitelist-task-5e3e38c2abdd`（本 PR · 10 起草 PR #357 同分支续棒 · reset 自 origin/master `0358c3b`） |
| 指令来源 | issue #337 维护者 comment [`6683541162`](https://github.com/Cyning12/ops-desk-api/issues/337#issuecomment-6683541162)（2026-11-06 19:15）：「HG-TASK-DRAFT 已签（PR #357 · squash 合并 `0358c3b`）…HG-GRAPH-MODULES 以 `none` 口径随档签认…请执行 20-R1：书面审查（审查文落盘出 PR 待审；task lint PASS 后出货）。审查重点：①六要素与闸表四列契约完整；②A1 锚点语义三要素自洽可执行；③刷新基线三子形态利弊对拍——特别关注重钉 `_BASE` 与 `_WAVE_TIP` 回归牙窗口的相容性…20-R1 出货时 lead 随档正式签 HG-DIFF-WHITELIST-DIAGNOSIS 与 HG-AUDIT-R1，通过即给 30 授权」· 签认链 = 维护者 2026-11-06 13:40 多选授权 + 19:04 大授权窗口 |

## 输入真值（已读/已跑）

- task 档全文（`0358c3b`）· issue #337 全线程 · PR #357 review `5799316636`（APPROVED 六条件 + lead 亲核实录）· 两枚闸源码全文 · 蓝本 `test_memory_injection_consumer.py`:585-631。
- **基线红复核（亲跑）**：`0358c3b` 干净树两枚用例复跑 **2 failed**，与档内登记逐字一致（:450 banned 22 件 / :554 banned 2 件）——题面缺陷现状无漂移。
- **固定波次窗模拟（亲跑 · 审查 §3.4）**：wave1 闭窗 `d337486..c17e63b` 15 文件 → violations 2 件（`backups/…snapshot` + `docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md`）→ 回归牙 fail（**F1 暗礁**）；wave2 闭窗 `a1591e9..63bad3d` 13 文件 → 全在白名单 → 态① pass。
- **溯源补证**：F1 两文件均出自 CLOSE commit `920c8e5` [00]（「CLOSE 归档 + 裁定链 invoke」· 同批 4 文件：snapshot / close invoke / query-coref 审查文 / task 归档更名——close invoke 已被 invoke 前缀覆盖，余两件漏登记）。

## 审查结论

**PASS · 零内容阻塞**——①六要素+闸表四列契约 PASS（HG-TASK-DRAFT / HG-GRAPH-MODULES 签认代录入闸表 · 引据 `6683541162` + `5799316636` · 非自签）；②A1 三要素（证据先于裁决/二值归因/闸语义不破）自洽可执行；③三子形态对拍：**①重钉 `_BASE` 与 `_WAVE_TIP` 回归牙窗口不相容**（保 tip → 窗倒置牙静默失效；重置 tip → 诚实重装结构性复发）/ **②改固定波次窗语义 = 正解**（与 lead 预告一致 · wave2 实测态① pass · wave1 实测 F1 暗礁须随修复登记两件）/ **③调 `_allowed` 面拍否**（banned/O2 空心化 + 白名单无界增长 = 恒绿失效）。

非阻塞 N1–N4（登记限定语写法 / 浅克隆 committed 面退化规格 / 闭窗后未来波次自注册新闸 / 题面编号锁定维持）。F1 = ②的落地必修项（已回填 R2 与验收 · 不构成退回 10）。

## 回填动作（本 PR 内 task 档）

| # | 项 | 位置 |
|---|----|------|
| 1 | HG-TASK-DRAFT / HG-GRAPH-MODULES 签认代录（引据在册） | 人工闸表 |
| 2 | 三子形态对拍 + F1 + N2 浅克隆规格 | R2「20-R1 对拍回填」块 |
| 3 | 固定窗态① pass + F1 登记验收条 | 验收标准 |
| 4 | 20 注 + 修订记录行 | 档头 / 修订记录 |

## 闸态（本 invoke 落盘时）

| 闸 | status | 说明 |
|----|--------|------|
| HG-TASK-DRAFT | approved | lead 签认 2026-11-06 · 依据 = issue #337 comment `6683541162` + PR #357 review `5799316636`（本 PR 代录入表） |
| HG-GRAPH-MODULES | approved | lead 签认 2026-11-06 · 依据同上 · `none` 口径（30 实扫出图谱面须回签） |
| HG-AUDIT-R1 | pending | 20-R1 审查文随本 PR 落盘 · 维护者令「20-R1 出货时 lead 随档正式签」——本帽不代签 |
| HG-DIFF-WHITELIST-DIAGNOSIS | pending | **设计闸** · 签认预告 = whitelist 过期→刷新基线 · 子形态=改固定波次窗语义（comment `6683541162`）· 本审查对拍支持（§3）· 正式签认随本 PR review——本帽不代签 |

- `npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_diff_whitelist_anchor_drift.md` → **VERIFY: BLOCKED**（两 approved / 两 pending）——与「签齐前 30 拒开工」一致。
- 30 预登记分支 `fix/diff-whitelist-anchor-drift` · 改动面 ⊆ 两枚测试文件（F1 两件登记 + 固定窗语义 + 红转绿双证据）。

## 自检

| 命令 | 结果 |
|------|------|
| `.venv/bin/python -m pytest tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire`（基线复核 · 只读） | **2 failed** 与档内登记逐字一致（预期红 · 修复前基线） |
| 固定波次窗模拟（git diff/log 复演 · 只读） | wave1 窗 F1 牙红 / wave2 窗态① pass（审查文 §3.4 实录） |
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_diff_whitelist_anchor_drift.md` | **PASS**（零 warn） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | **PASS**（scope all · 213/0） |
| `npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_diff_whitelist_anchor_drift.md` | **VERIFY: BLOCKED**（HG-AUDIT-R1 / HG-DIFF-WHITELIST-DIAGNOSIS pending · 与签认流程一致） |

## 禁区复核

- 未改 `app/` / `alembic/` / `scripts/` / `tests/`（仅 `docs/tasks/active/` + `docs/harness/reviews/` + `docs/harness/invokes/` 三文档面）。
- 未代签 HG-AUDIT-R1 / HG-DIFF-WHITELIST-DIAGNOSIS（维持 pending 待 lead 随本 PR 签）；HG-TASK-DRAFT / HG-GRAPH-MODULES 仅作**已发生签认的记录代录**（引据两元组在册 · 签认幂等锚五元组判同首次记录）。
- 审查全程只读 + git 复演（零仓内码改动 · 零测试改）。
